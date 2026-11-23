"""New events, regularly: release dates, yearly seasons, and dealing them first."""
import random
from datetime import date, datetime, timedelta, timezone

from app.game import week_service

NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)


def test_season_windows_including_the_new_year_wrap():
    black_friday = {'season_start': '11-20', 'season_end': '12-02'}
    new_year = {'season_start': '12-31', 'season_end': '01-10'}
    assert week_service.in_season(black_friday, date(2026, 11, 23))
    assert not week_service.in_season(black_friday, date(2026, 12, 3))
    assert week_service.in_season(new_year, date(2026, 12, 31)) and week_service.in_season(new_year, date(2027, 1, 5))
    assert not week_service.in_season(new_year, date(2027, 1, 11)) and not week_service.in_season(new_year, date(2026, 12, 30))
    assert week_service.in_season({}, date(2026, 6, 1))                     # no season: always


def test_release_dates_and_badges():
    old = {'title': 'Old'}
    drop = {'released_at': '2026-11-20T00:00:00+00:00'}
    future = {'released_at': '2026-11-30T00:00:00+00:00'}
    season = {'season_start': '11-20', 'season_end': '12-02', 'season_label': 'Black Friday', 'season_emoji': '🛍️'}
    assert week_service.released(old, NOW) and week_service.released(drop, NOW) and not week_service.released(future, NOW)
    assert week_service.badge(old, NOW) is None                              # older events never look "new"
    assert week_service.badge(drop, NOW) == {'emoji': '✨', 'label': 'New', 'kind': 'new'}
    assert week_service.badge(drop, NOW + timedelta(days=15)) is None        # new for two weeks
    assert week_service.badge(season, NOW) == {'emoji': '🛍️', 'label': 'Black Friday', 'kind': 'season'}


def _event(fake, eid, **kw):
    fake.rows('life_events').append({'id': eid, 'title': eid, 'description': '...', 'event_type': 'neutral', 'is_active': True, **kw})
    fake.rows('life_event_choices').extend([
        {'id': f'{eid}-a', 'life_event_id': eid, 'choice_label': 'A', 'outcome_description': 'a', 'cost': 0, 'benefit': 0, 'choice_order': 1, 'impact_sanity': 1},
        {'id': f'{eid}-b', 'life_event_id': eid, 'choice_label': 'B', 'outcome_description': 'b', 'cost': 0, 'benefit': 0, 'choice_order': 2, 'impact_sanity': -1},
    ])


def test_new_and_seasonal_events_are_dealt_first_and_unreleased_ones_never(fake_supabase, user_id, monkeypatch):
    monkeypatch.setattr(week_service, '_today', lambda: NOW.date())
    real_dt = week_service.datetime

    class FrozenDatetime(real_dt):
        @classmethod
        def now(cls, tz=None):
            return NOW

    monkeypatch.setattr(week_service, 'datetime', FrozenDatetime)
    for i in range(12):
        _event(fake_supabase, f'old{i}')
    _event(fake_supabase, 'bf', season_start='11-20', season_end='12-02', season_label='Black Friday', season_emoji='🛍️')
    _event(fake_supabase, 'valentine', season_start='02-07', season_end='02-15', season_label="Valentine's", season_emoji='💘')
    _event(fake_supabase, 'drop_live', released_at='2026-11-22T00:00:00+00:00')
    _event(fake_supabase, 'drop_next_week', released_at='2026-11-30T00:00:00+00:00')
    ctx = {'balance': 1000}
    for seed in range(20):
        cards = week_service._life_event_cards(user_id, random.Random(seed), ctx, 2)
        ids = {c['life_event_id'] for c in cards}
        assert ids == {'bf', 'drop_live'}, ids                             # the two with badges, every time
        assert {c['badge']['label'] for c in cards} == {'Black Friday', 'New'}
    # Once seen, they make way for the rest; out-of-season and unreleased never show.
    fake_supabase.rows('user_life_events').extend([
        {'id': 'u1', 'user_id': user_id, 'life_event_id': 'bf', 'choice_id': 'bf-a', 'created_at': '2026-11-22T00:00:00+00:00'},
        {'id': 'u2', 'user_id': user_id, 'life_event_id': 'drop_live', 'choice_id': 'drop_live-a', 'created_at': '2026-11-22T00:00:00+00:00'},
    ])
    dealt = set()
    for seed in range(40):
        dealt |= {c['life_event_id'] for c in week_service._life_event_cards(user_id, random.Random(seed), ctx, 2)}
    assert dealt and dealt <= {f'old{i}' for i in range(12)}
