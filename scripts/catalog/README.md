# Adding homes, businesses and luxury items

You write the item in a spreadsheet, the script turns it into SQL, and you run that SQL in the
Supabase SQL Editor. The script fills in the game numbers (rent, upkeep, business income,
running costs, depreciation, lease income) with the same rules as the rest of the catalog.

Run the commands from the `Wealthcraft-backend` folder. Only Python 3 is needed.

## Add new items

1. Start from an example: `python3 scripts/catalog/catalog.py template`
   (writes `scripts/catalog/examples/homes.csv`, `businesses.csv`, `luxury.csv`, `photos.csv`).
   Edit them in Excel, Google Sheets or any text editor and save as CSV.
2. Make the SQL:
   ```
   python3 scripts/catalog/catalog.py homes my_homes.csv -o homes.sql
   python3 scripts/catalog/catalog.py businesses my_businesses.csv -o businesses.sql
   python3 scripts/catalog/catalog.py luxury my_luxury.csv -o luxury.sql
   ```
3. Open the `.sql` file, copy everything, paste it in the Supabase SQL Editor and run it.

Names must be unique. A name that is already in the game is skipped; add `--update` to change
that item instead (its price, description, photo and the numbers worked out from them).

### Columns

| File | Required | Optional |
|---|---|---|
| homes | `name`, `type`, `price` | `bedrooms`, `location`, `description`, `image_url`, `image_credit`, `market_rent` |
| businesses | `name`, `price` | `risk` (low, medium, high, very_high; default medium), `description`, `image_url`, `image_credit`, `monthly_income` |
| luxury | `name`, `kind`, `price` | `description`, `image_url`, `image_credit`, `monthly_cost`, `lease_income`, `category` |

- Home `type`: studio, apartment, condo, loft, townhouse, duplex, cottage, bungalow, villa,
  beach house, lakehouse, penthouse, mansion, manor.
- Luxury `kind` decides the running costs and depreciation. See them all with
  `python3 scripts/catalog/catalog.py kinds`: cars (`car_small`, `car_mid`, `car_ev`, `car_suv`,
  `car_lux`, `car_classic`, `car_sport`, `car_super`), motorbikes (`moto_small`, `moto_mid`,
  `moto_big`), boats (`boat_small`, `boat_speed`, `boat_house`, `boat_sail`, `yacht_small`,
  `yacht`, `yacht_big`) and aircraft (`air_tiny`, `air_small`, `air_light`, `air_twin`, `jet`,
  `jet_big`, `heli`, `heli_big`).
- Motorbikes need "bike", "motorcycle" or "scooter" in the name, or profiles show them as cars
  (the script warns you).
- `market_rent`, `monthly_income`, `monthly_cost` and `lease_income` replace the worked-out number
  when you fill them in.

## Add or change photos

Make a CSV with `name`, `image_url` and, if the photo's licence asks for credit, `image_credit`
(for example `Photo: Jane Doe / CC BY 4.0`; the app shows it small on the card). Then:

```
python3 scripts/catalog/catalog.py photos my_photos.csv -o photos.sql
```

Run `photos.sql` in the SQL Editor. It finds each name in homes, businesses or luxury items, and
at the end lists any names it couldn't find (usually a typo). Lines without a link are skipped,
so you can fill in a list a bit at a time.

`scripts/catalog/data/photos_todo.csv` already lists every item in the game with an empty
`image_url` column, ready to fill in.

Photo tips: use `https://` links to the image itself (ending in .jpg, .png or .webp), about
1080 pixels wide, portrait or square. Only use photos you have the right to use: your own,
an advertiser's, or free-licence ones (Unsplash, Pexels, Wikimedia Commons public domain/CC0;
CC BY needs the `image_credit`).

## The starter catalog

`scripts/catalog/data/` holds the 121 homes, 116 businesses and 102 luxury items in
`supabase/migrations/20261207000000_showroom_catalog.sql`. To change them, edit the CSVs and
re-run the commands above with `--update`.
