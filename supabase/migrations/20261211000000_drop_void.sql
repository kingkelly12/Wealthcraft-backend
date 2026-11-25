-- The Void is gone from the app: drop its posts, reactions and counter function.
-- This permanently deletes every post and reaction. Safe to run more than once.
begin;

drop function if exists public.refresh_void_post_counts(uuid);
drop table if exists public.void_reactions;
drop table if exists public.void_posts;

commit;
