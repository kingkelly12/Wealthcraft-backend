#!/usr/bin/env python3
"""
Add homes, businesses and luxury items to the game from a spreadsheet (CSV).

    python3 scripts/catalog/catalog.py template                      # example CSVs in scripts/catalog/examples/
    python3 scripts/catalog/catalog.py homes my_homes.csv -o homes.sql
    python3 scripts/catalog/catalog.py businesses my_biz.csv -o biz.sql
    python3 scripts/catalog/catalog.py luxury my_cars.csv --update -o cars.sql
    python3 scripts/catalog/catalog.py photos my_photos.csv -o photos.sql   # name,image_url[,image_credit]

Then paste the .sql file into the Supabase SQL Editor and run it.

You write the name, price and a description. The script works out the game numbers with the
same rules as the rest of the catalog (rent and upkeep for homes, monthly income for businesses,
running costs, depreciation and lease income for luxury items). Any of those can be set by hand
with an optional column (see README.md).

Photos: put a link in image_url (and, if the photo's licence asks for credit, the credit in
image_credit; the app shows it small on the card). Or use the `photos` command to set photos
on items that already exist, from a list of names and links.
--update changes rows that already exist (matched by name) instead of skipping them.

Only the Python standard library is needed.
"""
import argparse, csv, hashlib, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# =============================================================================================
# The game's pricing rules
# =============================================================================================

def _jitter(name, lo=0.94, hi=1.06):
    """A small, stable variation per item, so two similar items don't have identical numbers."""
    h = int(hashlib.md5(name.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return lo + (hi - lo) * h


def _round(x):
    return int(5 * round(x / 5)) if x < 1000 else int(10 * round(x / 10))


# --- Homes ---------------------------------------------------------------------------------------
HOME_TYPES = ['studio', 'apartment', 'condo', 'loft', 'townhouse', 'duplex', 'cottage', 'bungalow',
              'villa', 'beach house', 'lakehouse', 'penthouse', 'mansion', 'manor']
UPKEEP = {  # (label, share of the price a month)
    'flat': [('Service charge', 0.00075), ('Insurance', 0.0002), ('Property rates', 0.0003)],
    'penthouse': [('Service charge', 0.0008), ('Insurance', 0.00018), ('Property rates', 0.00029)],
    'terrace': [('Estate fees', 0.00035), ('Insurance', 0.00018), ('Property rates', 0.0003), ('Maintenance', 0.00033)],
    'garden': [('Insurance', 0.00018), ('Property rates', 0.0003), ('Garden & maintenance', 0.0005)],
    'villa': [('Insurance', 0.00019), ('Property rates', 0.0003), ('Pool & garden', 0.00047), ('Caretaker', 0.00035)],
    'beach': [('Insurance', 0.0002), ('Property rates', 0.0003), ('Salt-air maintenance', 0.0005)],
    'lake': [('Insurance', 0.00019), ('Property rates', 0.00029), ('Dock & maintenance', 0.00054)],
    'mansion': [('Insurance', 0.00018), ('Property rates', 0.0003), ('Staff', 0.0011), ('Maintenance', 0.00055)],
    'manor': [('Insurance', 0.00018), ('Property rates', 0.00029), ('Staff', 0.001), ('Grounds', 0.00065)],
}
UPKEEP_BY_TYPE = {'studio': 'flat', 'apartment': 'flat', 'condo': 'flat', 'loft': 'flat', 'penthouse': 'penthouse',
                  'townhouse': 'terrace', 'duplex': 'terrace', 'cottage': 'garden', 'bungalow': 'garden', 'villa': 'villa',
                  'beach house': 'beach', 'lakehouse': 'lake', 'mansion': 'mansion', 'manor': 'manor'}
# Which household-bills table the backend uses (app/game/economy.py HOME_BILLS); others scale with the rent.
BILLS_TYPE = {'studio': 'studio', 'apartment': 'apartment', 'condo': 'condo', 'loft': 'condo', 'duplex': 'condo',
              'townhouse': 'house', 'bungalow': 'house', 'cottage': 'house', 'penthouse': 'penthouse'}


def home_numbers(name, htype, price):
    """Monthly rent it would let for (12% a year of the price for cheap homes, sliding to 6% for the
    most expensive) and its upkeep lines."""
    pos = min(max(math.log(price / 60000) / math.log(4_000_000 / 60000), 0), 1)
    rent = int(10 * round(price * (0.12 - 0.06 * pos) * _jitter(name) / 12 / 10))
    upkeep = [{'label': l, 'monthly': _round(price * share * _jitter(name + l, 0.9, 1.1))} for l, share in UPKEEP[UPKEEP_BY_TYPE[htype]]]
    return rent, upkeep


# --- Businesses -----------------------------------------------------------------------------------
RISKS = ['low', 'medium', 'high', 'very_high']
BASE_YIELD = {'low': 0.26, 'medium': 0.34, 'high': 0.42, 'very_high': 0.48}  # income a year as a share of price, for small businesses


def business_numbers(name, price, risk):
    """Average monthly income: riskier pays more, and the bigger the business the lower the yield
    (a $5k kiosk earns its price back far faster than a $2.5M resort)."""
    pos = min(max(math.log(price / 5000) / math.log(2_500_000 / 5000), 0), 1)
    monthly = _round(price * BASE_YIELD[risk] * (1 - 0.5 * pos) * _jitter(name, 0.92, 1.08) / 12)
    return max(monthly, 5)


def business_extras(price, monthly):
    roi = round(monthly * 12 / price * 100, 1)
    years = price / (monthly * 12)
    lo, hi = math.floor(years), math.ceil(years)
    ttr = 'about a year' if years < 1.5 else (f'{lo}-{hi} years' if lo != hi else f'{lo} years')
    avail = 2000 if price < 5000 else 800 if price < 50000 else 200 if price < 500000 else 50
    return roi, ttr, avail


# --- Luxury items ---------------------------------------------------------------------------------
# kind: (category, cost lines [(label, share of price a month, minimum)], depreciation a year,
#        service (share of price, every N months), lease (share of price a month, label) or None, lease wear)
KINDS = {
    'car_small':   ('cars', [('Fuel', 0.0090, 70), ('Insurance', 0.0050, 40), ('Parking', 0.0012, 15)], 0.15, (0.025, 6), (0.035, 'Rent it to a ride-hail driver'), 0.03),
    'car_mid':     ('cars', [('Fuel', 0.0055, 90), ('Insurance', 0.0040, 55), ('Parking', 0.0010, 20)], 0.15, (0.018, 6), (0.025, 'Rent it to a ride-hail driver'), 0.03),
    'car_ev':      ('cars', [('Charging', 0.0018, 40), ('Insurance', 0.0030, 60), ('Parking', 0.0006, 20)], 0.16, (0.006, 12), (0.022, 'Rent it on a car-share app'), 0.03),
    'car_suv':     ('cars', [('Fuel', 0.0050, 160), ('Insurance', 0.0045, 90), ('Parking', 0.0010, 30)], 0.16, (0.015, 6), (0.024, 'Hire it for safaris and road trips'), 0.03),
    'car_lux':     ('cars', [('Fuel', 0.0035, 250), ('Insurance', 0.0055, 300), ('Parking', 0.0010, 80)], 0.18, (0.014, 6), (0.022, 'Hire it for weddings and VIPs'), 0.03),
    'car_classic': ('cars', [('Fuel', 0.0025, 120), ('Classic insurance', 0.0025, 90), ('Garage', 0.0025, 100)], 0.00, (0.012, 12), (0.025, 'Hire it for weddings and photo shoots'), 0.02),
    'car_sport':   ('cars', [('Fuel', 0.0025, 250), ('Insurance', 0.0045, 300), ('Garage', 0.0008, 80)], 0.14, (0.018, 6), (0.026, 'Rent it for track days'), 0.04),
    'car_super':   ('cars', [('Fuel', 0.0015, 500), ('Insurance', 0.0048, 1500), ('Garage', 0.0005, 200)], 0.10, (0.020, 6), (0.025, 'Rent it for music videos and events'), 0.04),
    'moto_small':  ('motorbikes', [('Fuel', 0.0080, 20), ('Insurance', 0.0070, 15), ('Parking', 0.0020, 5)], 0.14, (0.030, 6), (0.045, 'Rent it to a delivery rider'), 0.04),
    'moto_mid':    ('motorbikes', [('Fuel', 0.0035, 40), ('Insurance', 0.0040, 45), ('Parking', 0.0010, 10)], 0.13, (0.020, 6), (0.035, 'Rent it to tourists'), 0.04),
    'moto_big':    ('motorbikes', [('Fuel', 0.0022, 60), ('Insurance', 0.0035, 85), ('Garage', 0.0009, 25)], 0.11, (0.016, 12), (0.028, 'Rent it for weekend tours'), 0.03),
    'boat_small':  ('boats', [('Fuel', 0.0050, 20), ('Insurance', 0.0040, 15), ('Storage', 0.0060, 30)], 0.12, (0.030, 12), (0.050, 'Rent it out at the beach'), 0.04),
    'boat_speed':  ('boats', [('Fuel', 0.0040, 80), ('Insurance', 0.0040, 70), ('Mooring', 0.0045, 80)], 0.13, (0.028, 6), (0.032, 'Charter it out on weekends'), 0.04),
    'boat_house':  ('boats', [('Mooring', 0.0060, 300), ('Insurance', 0.0030, 60), ('Maintenance', 0.0030, 80)], 0.06, (0.020, 12), (0.035, 'Let it as a floating holiday home'), 0.03),
    'boat_sail':   ('boats', [('Insurance', 0.0030, 60), ('Marina berth', 0.0040, 150), ('Sails & rigging', 0.0020, 40)], 0.08, (0.020, 12), (0.032, 'Charter it with a skipper'), 0.03),
    'yacht_small': ('boats', [('Fuel', 0.0028, 400), ('Insurance', 0.0025, 300), ('Marina berth', 0.0035, 500)], 0.10, (0.020, 6), (0.030, 'Charter it out'), 0.03),
    'yacht':       ('boats', [('Fuel', 0.0022, 2000), ('Insurance', 0.0012, 1200), ('Crew', 0.0060, 5000), ('Marina berth', 0.0020, 1800)], 0.10, (0.025, 12), (0.034, 'Charter it with crew'), 0.03),
    'yacht_big':   ('boats', [('Fuel', 0.0015, 15000), ('Insurance', 0.0010, 10000), ('Crew', 0.0035, 40000), ('Marina berth', 0.0012, 12000)], 0.08, (0.030, 12), (0.030, 'Charter it to billionaires'), 0.02),
    'air_tiny':    ('aircraft', [('Insurance', 0.0100, 30), ('Storage', 0.0060, 20)], 0.12, (0.050, 12), None, 0.0),
    'air_small':   ('aircraft', [('Fuel', 0.0030, 120), ('Insurance', 0.0035, 140), ('Hangar', 0.0035, 150)], 0.08, (0.030, 12), (0.030, 'Fly paying tourists'), 0.03),
    'air_light':   ('aircraft', [('Fuel', 0.0028, 600), ('Insurance', 0.0034, 700), ('Hangar', 0.0019, 450), ('Maintenance reserve', 0.0025, 500)], 0.06, (0.020, 12), (0.032, 'Lease it to a flight school'), 0.03),
    'air_twin':    ('aircraft', [('Fuel', 0.0030, 2000), ('Insurance', 0.0020, 1400), ('Hangar', 0.0012, 900), ('Pilot', 0.0020, 3000)], 0.07, (0.015, 12), (0.034, 'Fly island charters'), 0.03),
    'jet':         ('aircraft', [('Fuel', 0.0027, 9000), ('Insurance', 0.0013, 4500), ('Crew', 0.0030, 12000), ('Hangar', 0.0011, 4000)], 0.07, (0.012, 12), (0.036, 'Charter it by the hour'), 0.02),
    'jet_big':     ('aircraft', [('Fuel', 0.0018, 40000), ('Insurance', 0.0008, 15000), ('Crew', 0.0012, 40000), ('Hangar', 0.0005, 12000)], 0.06, (0.010, 12), (0.030, 'Charter it to the ultra-rich'), 0.02),
    'heli':        ('aircraft', [('Fuel', 0.0026, 1200), ('Insurance', 0.0022, 900), ('Hangar', 0.0016, 700), ('Pilot', 0.0035, 3500)], 0.08, (0.025, 6), (0.036, 'Fly tours and VIP transfers'), 0.03),
    'heli_big':    ('aircraft', [('Fuel', 0.0020, 4000), ('Insurance', 0.0016, 3500), ('Hangar', 0.0010, 2000), ('Pilot', 0.0018, 9000)], 0.08, (0.020, 6), (0.034, 'Fly VIP transfers'), 0.03),
    # Things you wear and carry. Watches hold their value; clothes do not.
    'watch':       ('accessories', [('Insurance', 0.0015, 3)], 0.00, (0.030, 36), None, 0.0),
    'jewellery':   ('accessories', [('Insurance', 0.0015, 3)], 0.05, (0.020, 24), None, 0.0),
    'bag':         ('accessories', [('Care & cleaning', 0.0030, 3)], 0.10, (0.030, 12), None, 0.0),
    'wear':        ('accessories', [('Cleaning', 0.0100, 3)], 0.35, (0.050, 12), None, 0.0),
    # Gadgets lose value fast.
    'phone':       ('gadgets', [('Phone plan', 0.0250, 25), ('Insurance', 0.0070, 6)], 0.30, (0.120, 12), None, 0.0),
    'device':      ('gadgets', [('Subscriptions', 0.0080, 5)], 0.25, (0.050, 12), None, 0.0),
    'creator':     ('gadgets', [('Insurance', 0.0040, 5)], 0.20, (0.040, 12), (0.045, 'Rent it out for shoots'), 0.08),
}


def luxury_numbers(name, price, kind):
    category, lines, dep, (svc_share, svc_every), lease, wear = KINDS[kind]
    costs = [{'label': l, 'monthly': _round(max(floor, price * share * _jitter(name + l, 0.92, 1.08)))} for l, share, floor in lines]
    lease_income, lease_label = (_round(price * lease[0] * _jitter(name, 0.9, 1.1)), lease[1]) if lease else (0, None)
    return {
        'category': category, 'costs': costs, 'monthly_cost': sum(c['monthly'] for c in costs), 'depreciation_rate': dep,
        'service_cost': _round(max(30, price * svc_share)), 'service_every_months': svc_every,
        'lease_income': lease_income, 'lease_label': lease_label, 'lease_wear': wear if lease else 0,
    }


# =============================================================================================
# CSV -> SQL
# =============================================================================================
def _q(v):
    if v is None or v == '':
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(round(v, 4))
    return "'" + str(v).replace("'", "''") + "'"


def _num(row, key, line, required=True):
    raw = (row.get(key) or '').replace(',', '').replace('$', '').strip()
    if not raw:
        if required:
            raise ValueError(f'line {line}: "{key}" is required')
        return None
    try:
        v = float(raw)
    except ValueError:
        raise ValueError(f'line {line}: "{key}" must be a number, got "{row.get(key)}"')
    return int(v) if v.is_integer() else v


def _read(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    return [({(k or '').strip().lower(): (v or '').strip() for k, v in r.items()}, i + 2) for i, r in enumerate(rows)]


def _photo(row, line):
    url, credit = row.get('image_url') or None, row.get('image_credit') or None
    if url and not url.startswith('https://'):
        raise ValueError(f'line {line}: image_url must start with https:// (got "{url[:60]}")')
    return url, credit


def build_homes(rows):
    out = []
    for row, line in rows:
        name = row.get('name') or ''
        if not name:
            raise ValueError(f'line {line}: "name" is required')
        htype = (row.get('type') or '').lower()
        if htype not in HOME_TYPES:
            raise ValueError(f'line {line}: type must be one of {", ".join(HOME_TYPES)} (got "{row.get("type")}")')
        price = _num(row, 'price', line)
        rent, upkeep = home_numbers(name, htype, price)
        rent = _num(row, 'market_rent', line, False) or rent
        url, credit = _photo(row, line)
        out.append({'name': name, 'home_type': htype, 'bills_type': BILLS_TYPE.get(htype), 'price': price, 'market_rent': rent,
                    'bedrooms': int(_num(row, 'bedrooms', line, False) or 1), 'location': row.get('location') or 'Downtown',
                    'description': row.get('description') or None, 'upkeep': json.dumps(upkeep), 'image_url': url, 'image_credit': credit})
    return 'home_listings', out, {'upkeep': 'jsonb', 'price': 'numeric', 'market_rent': 'numeric', 'bedrooms': 'int'}, \
        ['price', 'market_rent', 'bills_type', 'bedrooms', 'location', 'description', 'upkeep', 'image_url', 'image_credit']


def build_businesses(rows):
    out = []
    for row, line in rows:
        name = row.get('name') or ''
        if not name:
            raise ValueError(f'line {line}: "name" is required')
        risk = (row.get('risk') or 'medium').lower().replace(' ', '_')
        if risk not in RISKS:
            raise ValueError(f'line {line}: risk must be one of {", ".join(RISKS)} (got "{row.get("risk")}")')
        price = _num(row, 'price', line)
        monthly = _num(row, 'monthly_income', line, False) or business_numbers(name, price, risk)
        roi, ttr, avail = business_extras(price, monthly)
        url, credit = _photo(row, line)
        out.append({'name': name, 'category': 'business', 'price': price, 'monthly_income': monthly, 'description': row.get('description') or None,
                    'risk_level': risk, 'roi': roi, 'time_to_return': ttr, 'availability': avail, 'total_supply': avail,
                    'educational_tier': 'beginner', 'image_url': url, 'image_credit': credit})
    return 'assets', out, {'price': 'numeric', 'monthly_income': 'numeric', 'roi': 'numeric', 'availability': 'int', 'total_supply': 'int'}, \
        ['price', 'monthly_income', 'description', 'risk_level', 'roi', 'time_to_return', 'image_url', 'image_credit']


def build_luxury(rows):
    out = []
    for row, line in rows:
        name = row.get('name') or ''
        if not name:
            raise ValueError(f'line {line}: "name" is required')
        kind = (row.get('kind') or '').lower()
        if kind not in KINDS:
            raise ValueError(f'line {line}: kind must be one of {", ".join(KINDS)} (got "{row.get("kind")}")')
        price = _num(row, 'price', line)
        n = luxury_numbers(name, price, kind)
        monthly_override = _num(row, 'monthly_cost', line, False)
        if monthly_override:
            n['monthly_cost'], n['costs'] = monthly_override, [{'label': 'Running costs', 'monthly': monthly_override}]
        url, credit = _photo(row, line)
        out.append({'name': name, 'category': row.get('category') or n['category'], 'base_price': price, 'monthly_cost': n['monthly_cost'],
                    'description': row.get('description') or None, 'depreciation_rate': n['depreciation_rate'], 'costs': json.dumps(n['costs']),
                    'service_cost': n['service_cost'], 'service_every_months': n['service_every_months'],
                    'lease_income': _num(row, 'lease_income', line, False) or n['lease_income'], 'lease_label': n['lease_label'],
                    'lease_wear': n['lease_wear'], 'image_url': url, 'image_credit': credit})
    return 'liability_items', out, {'base_price': 'numeric', 'monthly_cost': 'numeric', 'depreciation_rate': 'numeric', 'costs': 'jsonb',
                                    'service_cost': 'numeric', 'service_every_months': 'int', 'lease_income': 'numeric', 'lease_wear': 'numeric'}, \
        ['base_price', 'monthly_cost', 'description', 'depreciation_rate', 'costs', 'service_cost', 'service_every_months',
         'lease_income', 'lease_label', 'lease_wear', 'image_url', 'image_credit']


def to_sql(table, rows, casts, update_cols, update, title):
    if not rows:
        return ''
    cols = list(rows[0].keys())
    values = ',\n'.join('  (' + ', '.join(_q(r[c]) for c in cols) + ')' for r in rows)
    select = ', '.join(f'v.{c}::{casts[c]}' if c in casts else f'v.{c}' for c in cols)
    conflict = ('do update set ' + ', '.join(f'{c} = excluded.{c}' for c in update_cols)) if update else 'do nothing'
    return (f"-- {title}: {len(rows)} rows ({'new rows added, existing names updated' if update else 'existing names are skipped'})\n"
            f"insert into public.{table} ({', '.join(cols)})\n"
            f"select {select}\nfrom (values\n{values}\n) as v({', '.join(cols)})\n"
            f"on conflict (name) {conflict};\n")


def photos_sql(rows):
    """Set photos on items that already exist, by name, whichever table they're in."""
    out = []
    for row, line in rows:
        name = row.get('name') or ''
        if not name:
            raise ValueError(f'line {line}: "name" is required')
        url, credit = _photo(row, line)
        if not url:
            continue  # no link yet on this line: nothing to set
        out.append((name, url, credit))
    if not out:
        raise ValueError('no rows with an image_url to set')
    values = ',\n'.join(f'  ({_q(n)}, {_q(u)}, {_q(c)})' for n, u, c in out)
    sql = f"-- Photos for {len(out)} items, matched by name in homes, businesses and luxury items.\n"
    for table in ('home_listings', 'assets', 'liability_items'):
        sql += (f"update public.{table} t set image_url = v.image_url, image_credit = v.image_credit\n"
                f"from (values\n{values}\n) as v(name, image_url, image_credit)\nwhere t.name = v.name;\n\n")
    return sql, out, values


HEADER = """-- Made by scripts/catalog/catalog.py. Paste it in the Supabase SQL Editor and run it.
-- Safe to run more than once.
begin;

-- Photo columns (no-ops once they exist).
alter table public.assets add column if not exists image_url text;
alter table public.assets add column if not exists image_credit text;
alter table public.home_listings add column if not exists image_credit text;
alter table public.liability_items add column if not exists image_credit text;

"""
TABLES = {'public.home_listings', 'public.assets', 'public.liability_items'}


def check_editor_safe(sql):
    """The Supabase SQL Editor reads 'into X' and 'table X' as table names, even inside text,
    and fails when X isn't one. Catch that here, with the words to reword."""
    bad = sorted({m.group(0) for m in re.finditer(r'\b(?:into|table)\s+([\w.]+)', sql, re.I) if m.group(1) not in TABLES})
    if bad:
        raise ValueError('reword these phrases in your descriptions or names (the Supabase SQL Editor misreads them): ' + '; '.join(f'"{b}"' for b in bad))


EXAMPLES = {
    'homes.csv': [
        ['name', 'type', 'price', 'bedrooms', 'location', 'description', 'image_url', 'image_credit'],
        ['Sunrise Loft', 'loft', '245000', '2', 'Arts Quarter', 'Brick walls, giant windows and a neighbour who plays saxophone.', '', ''],
        ['Harbour Studio Two', 'studio', '99000', '0', 'Harbourside', 'Tiny, bright and smells faintly of the sea.', '', ''],
    ],
    'businesses.csv': [
        ['name', 'price', 'risk', 'description', 'image_url', 'image_credit'],
        ['Waffle Cart', '2600', 'high', 'Hot waffles, long queues on cold mornings.', '', ''],
        ['Laundry Pickup Service', '18000', 'medium', 'Collect, wash, fold, deliver. Busy parents love you.', '', ''],
    ],
    'luxury.csv': [
        ['name', 'kind', 'price', 'description', 'image_url', 'image_credit'],
        ['Electric Cargo Bike', 'moto_small', '3800', 'Groceries, kids or a sofa. Probably not the sofa.', '', ''],
        ['Island Floatplane', 'air_light', '610000', 'Land on the lagoon, taxi to the beach bar.', '', ''],
    ],
    'photos.csv': [
        ['name', 'image_url', 'image_credit'],
        ['Studio Flat', 'https://example.com/your-studio-photo.jpg', ''],
        ['Private Jet', 'https://example.com/your-jet-photo.jpg', 'Photo: Jane Doe / CC BY 4.0'],
    ],
}


def main():
    ap = argparse.ArgumentParser(description='Turn a CSV of homes, businesses or luxury items into SQL for the Supabase SQL Editor.')
    ap.add_argument('what', choices=['homes', 'businesses', 'luxury', 'photos', 'template', 'kinds'])
    ap.add_argument('csv', nargs='?')
    ap.add_argument('-o', '--out', help='write the SQL here (default: print it)')
    ap.add_argument('--update', action='store_true', help='update rows that already exist (same name) instead of skipping them')
    ap.add_argument('--no-header', action='store_true', help='leave out begin/commit and the photo columns (for joining files)')
    a = ap.parse_args()

    if a.what == 'template':
        folder = os.path.join(HERE, 'examples'); os.makedirs(folder, exist_ok=True)
        for fname, rows in EXAMPLES.items():
            with open(os.path.join(folder, fname), 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerows(rows)
        print(f'Example CSVs written to {folder}')
        return
    if a.what == 'kinds':
        for k, v in KINDS.items():
            print(f'{k:12} {v[0]:9} depreciation {int(v[2] * 100)}%/yr  lease: {v[4][1] if v[4] else "-"}')
        return
    if not a.csv:
        ap.error('give the CSV file to read')

    if a.what == 'photos':
        try:
            body, rows, values = photos_sql(_read(a.csv))
            # After commit: list any names that matched nothing (typos), so they don't fail silently.
            missing = (f"select v.name as \"not found (check the spelling)\" from (values\n{values}\n) as v(name, image_url, image_credit)\n"
                       "where not exists (select 1 from public.home_listings h where h.name = v.name)\n"
                       "  and not exists (select 1 from public.assets a where a.name = v.name)\n"
                       "  and not exists (select 1 from public.liability_items l where l.name = v.name);\n")
            sql = HEADER + body + 'commit;\n\n' + missing
            check_editor_safe(sql)
        except ValueError as e:
            sys.exit(f'Error: {e}')
        if a.out:
            open(a.out, 'w', encoding='utf-8').write(sql)
            print(f'{len(rows)} photos written to {a.out}. Paste it in the Supabase SQL Editor and run it; it lists any names it could not find.', file=sys.stderr)
        else:
            print(sql)
        return

    builder = {'homes': build_homes, 'businesses': build_businesses, 'luxury': build_luxury}[a.what]
    try:
        table, rows, casts, update_cols, = builder(_read(a.csv))
        names = [r['name'] for r in rows]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            raise ValueError('these names appear more than once (names must be unique): ' + ', '.join(dupes))
        body = to_sql(table, rows, casts, update_cols, a.update, a.what.capitalize())
        sql = body if a.no_header else HEADER + body + '\ncommit;\n'
        check_editor_safe(sql)
    except ValueError as e:
        sys.exit(f'Error: {e}')
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(sql)
        print(f'{len(rows)} {a.what} written to {a.out}. Paste it in the Supabase SQL Editor and run it.', file=sys.stderr)
    else:
        print(sql)


if __name__ == '__main__':
    main()
