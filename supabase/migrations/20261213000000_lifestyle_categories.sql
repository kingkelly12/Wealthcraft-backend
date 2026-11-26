-- =============================================================================
-- Lifestyle categories: cars, motorbikes, boats, aircraft, accessories, gadgets
-- * "vehicle" becomes two categories, cars and motorbikes; "boat" -> boats; fashion -> accessories; tech -> gadgets.
-- * "wellness" is removed (its one item is deleted unless a player owns it).
-- * 42 new items: 21 accessories and 21 gadgets (from scripts/catalog/data/accessories_gadgets.csv).
-- Safe to run more than once.
-- =============================================================================
begin;

alter table public.liability_items add column if not exists image_credit text;

update public.liability_items set category = 'motorbikes' where category = 'vehicle' and name ~* '(bike|motorcycle|scooter)';
update public.liability_items set category = 'cars' where category = 'vehicle';
update public.liability_items set category = 'boats' where category = 'boat';
update public.liability_items set category = 'accessories' where category = 'fashion';
update public.liability_items set category = 'gadgets' where category = 'tech';

-- Wellness: drop saved showroom deals and wishlist entries for it, then the item itself.
delete from public.showroom_deals d using public.liability_items l
 where d.kind = 'item' and d.item_id::text = l.id::text and l.category = 'wellness';
delete from public.showroom_wishlist w using public.liability_items l
 where w.kind = 'item' and w.item_id::text = l.id::text and l.category = 'wellness';
delete from public.showroom_seen s using public.liability_items l
 where s.kind = 'item' and s.item_id::text = l.id::text and l.category = 'wellness';
delete from public.liability_items l
 where l.category = 'wellness' and not exists (select 1 from public.player_liabilities p where p.liability_id = l.id);

-- Luxury: 42 rows (existing names are skipped)
insert into public.liability_items (name, category, base_price, monthly_cost, description, depreciation_rate, costs, service_cost, service_every_months, lease_income, lease_label, lease_wear, image_url, image_credit)
select v.name, v.category, v.base_price::numeric, v.monthly_cost::numeric, v.description, v.depreciation_rate::numeric, v.costs::jsonb, v.service_cost::numeric, v.service_every_months::int, v.lease_income::numeric, v.lease_label, v.lease_wear::numeric, v.image_url, v.image_credit
from (values
  ('Gold Hoop Earrings', 'accessories', 320, 5, 'Small hoops with big opinions.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 30, 24, 0, null, 0, null, null),
  ('Silk Scarf', 'accessories', 380, 5, 'Wear it as a scarf, a headband or a personality.', 0.35, '[{"label": "Cleaning", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Designer Sunglasses', 'accessories', 420, 5, 'Instantly 40% more mysterious.', 0.1, '[{"label": "Care & cleaning", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Limited Edition Sneakers', 'accessories', 450, 5, 'You will walk around puddles like they are lava.', 0.35, '[{"label": "Cleaning", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Leather Wallet', 'accessories', 480, 5, 'A beautiful home for very little money.', 0.1, '[{"label": "Care & cleaning", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Statement Jacket', 'accessories', 950, 10, 'People will ask where you got it. You will enjoy this far too much.', 0.35, '[{"label": "Cleaning", "monthly": 10}]', 50, 12, 0, null, 0, null, null),
  ('Leather Boots', 'accessories', 680, 5, 'Break them in for a month. Then they love you forever.', 0.35, '[{"label": "Cleaning", "monthly": 5}]', 35, 12, 0, null, 0, null, null),
  ('Tailored Suit', 'accessories', 1400, 15, 'You look like you have a plan. You do not need a plan in this suit.', 0.35, '[{"label": "Cleaning", "monthly": 15}]', 70, 12, 0, null, 0, null, null),
  ('Evening Gown', 'accessories', 1800, 20, 'For galas, weddings and dramatic exits.', 0.35, '[{"label": "Cleaning", "monthly": 20}]', 90, 12, 0, null, 0, null, null),
  ('Cashmere Overcoat', 'accessories', 2200, 25, 'So soft strangers want to touch it. Please do not let them.', 0.35, '[{"label": "Cleaning", "monthly": 25}]', 110, 12, 0, null, 0, null, null),
  ('Weekend Leather Duffel', 'accessories', 1100, 5, 'Packed for a getaway you have not booked.', 0.1, '[{"label": "Care & cleaning", "monthly": 5}]', 35, 12, 0, null, 0, null, null),
  ('Everyday Designer Tote', 'accessories', 1900, 5, 'Holds your whole life and three old receipts.', 0.1, '[{"label": "Care & cleaning", "monthly": 5}]', 55, 12, 0, null, 0, null, null),
  ('Silver Signet Ring', 'accessories', 650, 5, 'Instant old money. The money is not included.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 30, 24, 0, null, 0, null, null),
  ('Pearl Necklace', 'accessories', 1600, 5, 'Your grandma will approve. Loudly.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 30, 24, 0, null, 0, null, null),
  ('Gold Chain', 'accessories', 3200, 5, 'Heavy enough to count as a workout.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 65, 24, 0, null, 0, null, null),
  ('Diamond Stud Earrings', 'accessories', 4800, 5, 'Tiny, sparkly and not tiny in price.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 95, 24, 0, null, 0, null, null),
  ('Diamond Tennis Bracelet', 'accessories', 9500, 15, 'You will wave at people for no reason.', 0.05, '[{"label": "Insurance", "monthly": 15}]', 190, 24, 0, null, 0, null, null),
  ('Automatic Dress Watch', 'accessories', 2800, 5, 'Tells the time and also that you made it.', 0.0, '[{"label": "Insurance", "monthly": 5}]', 85, 36, 0, null, 0, null, null),
  ('Dive Watch', 'accessories', 8500, 10, 'Waterproof to depths you will never visit.', 0.0, '[{"label": "Insurance", "monthly": 10}]', 255, 36, 0, null, 0, null, null),
  ('Gold Chronograph Watch', 'accessories', 24000, 35, 'Three little dials. You use none of them.', 0.0, '[{"label": "Insurance", "monthly": 35}]', 720, 36, 0, null, 0, null, null),
  ('Skeleton Tourbillon Watch', 'accessories', 85000, 125, 'You can see every gear spending your money.', 0.0, '[{"label": "Insurance", "monthly": 125}]', 2550, 36, 0, null, 0, null, null),
  ('Wireless Earbuds', 'gadgets', 220, 5, 'Lose one within a month. It is tradition.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Smart Ring', 'gadgets', 350, 5, 'Tracks your sleep and silently judges it.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Mechanical Keyboard', 'gadgets', 260, 5, 'Loud enough that coworkers know you are working.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Noise-cancelling Headphones', 'gadgets', 420, 5, 'Cancels noise, small talk and your flatmate.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Portable Speaker', 'gadgets', 280, 5, 'Every park is now your personal party.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Smartwatch', 'gadgets', 480, 5, 'Tells you to stand up. Frequently.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Handheld Gaming Console', 'gadgets', 550, 5, 'Just one more level. It is 3am.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('E-reader', 'gadgets', 200, 5, 'Carries a thousand books you intend to read.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Home Games Console', 'gadgets', 600, 5, 'Ruins sleep schedules since the first level.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Drawing Tablet', 'gadgets', 900, 5, 'Draw masterpieces. Mostly draw cats.', 0.2, '[{"label": "Insurance", "monthly": 5}]', 35, 12, 40, 'Rent it out for shoots', 0.08, null, null),
  ('Camera Drone', 'gadgets', 1300, 5, 'Cinematic shots of your own roof.', 0.2, '[{"label": "Insurance", "monthly": 5}]', 50, 12, 60, 'Rent it out for shoots', 0.08, null, null),
  ('Mirrorless Camera', 'gadgets', 2100, 10, 'Makes even your lunch look expensive.', 0.2, '[{"label": "Insurance", "monthly": 10}]', 85, 12, 90, 'Rent it out for shoots', 0.08, null, null),
  ('Studio Podcast Kit', 'gadgets', 1100, 5, 'Your hot takes, now in high definition.', 0.2, '[{"label": "Insurance", "monthly": 5}]', 45, 12, 45, 'Rent it out for shoots', 0.08, null, null),
  ('Cinema Camera', 'gadgets', 8500, 35, 'For when your phone is just not serious enough.', 0.2, '[{"label": "Insurance", "monthly": 35}]', 340, 12, 385, 'Rent it out for shoots', 0.08, null, null),
  ('Foldable Smartphone', 'gadgets', 1800, 60, 'A phone that becomes a slightly bigger phone.', 0.3, '[{"label": "Phone plan", "monthly": 45}, {"label": "Insurance", "monthly": 15}]', 215, 12, 0, null, 0, null, null),
  ('Flagship Smartphone Pro', 'gadgets', 1500, 45, 'Three cameras, so every blurry photo is blurry from three angles.', 0.3, '[{"label": "Phone plan", "monthly": 35}, {"label": "Insurance", "monthly": 10}]', 180, 12, 0, null, 0, null, null),
  ('Ultrabook Laptop', 'gadgets', 1700, 15, 'Thin, fast and perfect for looking busy in cafes.', 0.25, '[{"label": "Subscriptions", "monthly": 15}]', 85, 12, 0, null, 0, null, null),
  ('Gaming PC', 'gadgets', 2800, 25, 'Glows in six colours. Runs everything. Heats the room.', 0.25, '[{"label": "Subscriptions", "monthly": 25}]', 140, 12, 0, null, 0, null, null),
  ('Giant OLED Television', 'gadgets', 3200, 25, 'So big your neighbours can watch too.', 0.25, '[{"label": "Subscriptions", "monthly": 25}]', 160, 12, 0, null, 0, null, null),
  ('VR Headset', 'gadgets', 700, 5, 'Punch walls in a whole new world.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 35, 12, 0, null, 0, null, null),
  ('Home Cinema System', 'gadgets', 6500, 55, 'Surround sound so good the pizza feels nervous.', 0.25, '[{"label": "Subscriptions", "monthly": 55}]', 325, 12, 0, null, 0, null, null)
) as v(name, category, base_price, monthly_cost, description, depreciation_rate, costs, service_cost, service_every_months, lease_income, lease_label, lease_wear, image_url, image_credit)
on conflict (name) do nothing;

commit;

select category, count(*) as items from public.liability_items group by category order by category;
