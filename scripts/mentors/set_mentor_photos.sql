-- Mentor photos. Upload a photo for each mentor to Supabase Storage, bucket
-- "avatars" (any folder), with "Coach Chen", "Tasha" or "Parent" in the file name
-- (capitals, spaces and .jpg/.png don't matter). Then run this. Safe to re-run.
update public.mentors m
set avatar_url = 'https://zirfajyutvczzixxfxci.supabase.co/storage/v1/object/public/avatars/'
                 || replace(o.name, ' ', '%20')            -- spaces must be encoded in a link
from storage.objects o,
     (values ('11111111-1111-1111-1111-111111111111', '%coach%chen%'),
             ('22222222-2222-2222-2222-222222222222', '%tasha%'),
             ('33333333-3333-3333-3333-333333333333', '%parent%')) as p(id, pattern)
where m.id::text = p.id and o.bucket_id = 'avatars' and o.name ilike p.pattern;

-- Check: all three should end in your file's name.
select name, avatar_url from public.mentors order by name;
