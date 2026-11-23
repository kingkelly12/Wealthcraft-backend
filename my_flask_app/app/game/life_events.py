"""
Life event rules shared by the weekly deck (week_service), the event screen
(routes/life_event_routes) and the daily auto-resolve job
(jobs/event_deadlines). Keep effects in ONE place so the paths can't
drift apart.

A choice's effect is exactly what is stored on that choice:
    cash   = benefit - cost
    sanity = impact_sanity
    income = impact_income   (permanent monthly change)

There is deliberately no fallback to the event's own impact_* columns. The old
"choice is 0 -> use the event's value" rule made a choice that was meant to have
no effect inherit the event's hit (e.g. both sides of "The Dental Gamble" got
-10 sanity). Every seeded choice now carries its own values.
"""
import uuid
from decimal import Decimal
from typing import Dict, List

DEFAULT_TIME_LIMIT_SECONDS = 7 * 24 * 3600


def choice_effects(choice: Dict) -> Dict:
    return {
        'cash': Decimal(str(choice.get('benefit') or 0)) - Decimal(str(choice.get('cost') or 0)),
        'sanity': int(choice.get('impact_sanity') or 0),
        'income': Decimal(str(choice.get('impact_income') or 0)),
    }


def cash_due(cash: Decimal, balance: Decimal, other_choices_cash) -> Decimal:
    """
    What a choice actually costs given the player's balance.

    Raises LookupError if the player can't afford it but another choice is
    free (they should pick that one). If every choice costs money, they pay
    what they have instead of getting stuck on an event they can never resolve.
    """
    if cash >= 0 or -cash <= balance:
        return cash
    if any(c >= 0 for c in other_choices_cash):
        raise LookupError('unaffordable')
    return -balance


def default_choice(choices: List[Dict]) -> Dict:
    """
    The choice the game makes for a player who ignored the event: the cheapest
    one (doing nothing usually costs nothing), and among equally cheap ones the
    one with the worst sanity effect, because ignoring a problem has a price
    ("Ignore it and pray" rather than "Book the dentist").
    """
    return max(choices, key=lambda c: (choice_effects(c)['cash'],
                                       -choice_effects(c)['sanity'],
                                       -(c.get('choice_order') or 0)))


class AlreadyResolved(Exception):
    """The pending event was answered elsewhere first (another request, the deck, the job)."""


def resolve(supabase, user_id: str, row_id: str, event: Dict, choice: Dict, choices: List[Dict],
            auto: bool = False) -> Dict:
    """
    Answer one pending user_life_events row and apply the choice's effects.

    Order matters: affordability is checked first (LookupError, nothing changed),
    then the row is claimed atomically (AlreadyResolved if someone got there
    first), then money moves; if the money fails the claim is released.
    Returns the effects actually applied.
    """
    from app.services.balance_service import BalanceService
    from app.services.profile_service import ProfileService

    effects = choice_effects(choice)
    balance = BalanceService.get_current_balance(user_id)
    cash = cash_due(effects['cash'], balance,
                    [choice_effects(c)['cash'] for c in choices if str(c['id']) != str(choice['id'])])

    claim = supabase.table('user_life_events') \
        .update({'choice_id': str(choice['id']), 'was_auto_selected': auto}) \
        .eq('id', row_id).is_('choice_id', 'null').execute()
    if not claim.data:
        raise AlreadyResolved()

    reason = f"{event['title']} - {choice['choice_label']}" + (' (ignored)' if auto else '')
    try:
        if cash > 0:
            BalanceService.add_balance(user_id, cash, reason, category='life_event')
        elif cash < 0:
            BalanceService.subtract_balance(user_id, -cash, reason, category='life_event')
    except Exception:
        supabase.table('user_life_events').update({'choice_id': None, 'was_auto_selected': False}) \
            .eq('id', row_id).eq('choice_id', str(choice['id'])).execute()
        raise

    income = effects['income']
    if income:
        ProfileService.update_monthly_income(uuid.UUID(str(user_id)), float(income))

    rows = supabase.table('profiles').select('sanity').eq('user_id', str(user_id)).limit(1).execute().data or []
    before = rows[0].get('sanity') if rows else None
    before = 100 if before is None else int(before)
    new_sanity = before
    if effects['sanity']:
        res = supabase.rpc('adjust_sanity', {'p_user_id': str(user_id), 'p_delta': effects['sanity']}).execute()
        new_sanity = int(res.data) if res.data is not None else before

    return {
        'cash': cash,
        'income': income,
        'sanity_before': before,
        'new_sanity': new_sanity,
        # Same rule as the weekly deck: game over when sanity drops to 0 now.
        'game_over': new_sanity <= 0 < before,
    }
