-- Every player is on game time: new sign-ups get a clock row, and existing
-- profiles without one get one now. (The calendar jobs are retired.)
-- New auth user → profile + wallet. Username collisions get a numeric suffix
-- instead of aborting the sign-up (the old trigger failed sign-up with a 500).
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
declare
  v_base     text;
  v_username text;
  v_try      integer := 0;
  -- Starting cash for a new player. Tune to taste.
  c_starting_balance constant numeric := 5000;
begin
  v_base := coalesce(
    nullif(new.raw_user_meta_data ->> 'username', ''),
    nullif(split_part(coalesce(new.email, ''), '@', 1), ''),
    'player'
  );
  v_base := left(regexp_replace(v_base, '[^A-Za-z0-9_.]', '', 'g'), 40);
  if char_length(v_base) < 3 then
    v_base := v_base || 'player';
  end if;
  v_username := v_base;

  while exists (select 1 from public.profiles where username = v_username) loop
    v_try := v_try + 1;
    v_username := v_base || (floor(random() * 9000) + 1000)::int::text;
    if v_try > 20 then
      v_username := v_base || replace(gen_random_uuid()::text, '-', '');
      exit;
    end if;
  end loop;

  insert into public.profiles (user_id, username, profile_picture_url)
  values (new.id, v_username, new.raw_user_meta_data ->> 'avatar_url');

  insert into public.user_balances (user_id, current_balance)
  values (new.id, c_starting_balance);

  insert into public.transactions (user_id, type, category, amount, description)
  values (new.id, 'income', 'starting_balance', c_starting_balance, 'Starting cash');

  -- Every player is on game time from the start (week 1, a day's weeks ready to play).
  insert into public.player_game_clock (user_id) values (new.id) on conflict do nothing;

  return new;
end $$;


insert into public.player_game_clock (user_id)
select user_id from public.profiles
on conflict do nothing;
