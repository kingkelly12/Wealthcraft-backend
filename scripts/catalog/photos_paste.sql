-- Photos straight from the CSV, for the Supabase SQL Editor.
-- Paste the whole CSV (header line included) between the two $csv$ lines below, then Run.
-- Lines with no link are skipped. Safe to run more than once.
-- It ends with "Photos set: N" and a line for each name it couldn't find (check the spelling).

alter table public.assets add column if not exists image_url text;
alter table public.assets add column if not exists image_credit text;
alter table public.home_listings add column if not exists image_credit text;
alter table public.liability_items add column if not exists image_credit text;

with raw(t) as (values ($csv$
name,image_url,image_credit,what
$csv$)),
lines as (
  select replace(btrim(l, E' \r\t'), '"', '') as l
  from raw, regexp_split_to_table(raw.t, E'\n') as l
),
linked as (
  -- Full lines (name,link,credit,what) keep their credit; shorter or tab-separated lines still work.
  select l, regexp_match(l, '^([^,;\t]*),(https?://.*),([^,/]*),([^,/]*)$') as m
  from lines where l ~* 'https?://'
),
v as (
  select distinct on (name) name, image_url, image_credit from (
    select btrim(coalesce(m[1], substring(l from '^([^,;\t]*)'))) as name,
           btrim(coalesce(m[2], regexp_replace(substring(l from '(https?://.*)$'), '([,;\t][^,;\t/]*)+$', ''))) as image_url,
           nullif(btrim(m[3]), '') as image_credit
    from linked
  ) x where name <> ''
),
h as (update public.home_listings t set image_url = v.image_url, image_credit = v.image_credit from v where t.name = v.name returning t.name),
a as (update public.assets t set image_url = v.image_url, image_credit = v.image_credit from v where t.name = v.name returning t.name),
li as (update public.liability_items t set image_url = v.image_url, image_credit = v.image_credit from v where t.name = v.name returning t.name)
select 'Links found: ' || (select count(*) from v)::text
       || ' · Photos set: ' || ((select count(*) from h) + (select count(*) from a) + (select count(*) from li))::text as result
union all
select 'Not found (check the spelling): ' || v.name from v
where v.name not in (select name from h union all select name from a union all select name from li);
