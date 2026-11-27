"""
Mentor service: turns a player's financial state into mentor messages.

Flow
----
1. analyze_player_finances()  -> metrics dict (also fed to the AI chat)
2. check_triggers()           -> candidate triggers, each tied to a mentor role
3. pick_daily_triggers()      -> drops triggers on cooldown, max 1 per mentor
4. generate_personalized_message() -> fills the mentor_messages template
5. send_mentor_message()      -> stores a player_mentor_interactions row + push

Triggers map 1:1 onto mentor_messages.trigger_type rows seeded by
seed_mentors.sql, and mentor_role onto mentors.role
('strategic' = Coach Chen, 'risk_analyst' = Tasha, 'emotional' = Parent).
"""
import logging
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from sqlalchemy import func

from app import db
from app.models.mentor import Mentor
from app.models.mentor_message import MentorMessage
from app.models.player_mentor_interaction import PlayerMentorInteraction
from app.models.profile import Profile
from app.models.user_asset import UserAsset
from app.models.liability import Liability
from app.models.user_balance import UserBalance

logger = logging.getLogger(__name__)

# Transaction categories that move money between the player's own pockets
# (cash <-> assets, escrow, loan principal). They are not income or spending,
# so they must not count toward cash flow / expense ratio. Without this, buying
# an index fund looked like "overspending" and triggered negative-cash-flow nags.
# 'new_life' is the reset to a background's starting cash (a +$15,000 "income" for Rich Parents made
# high_savings_rate fire at 3,750%; a reset from more cash looked like a huge expense).
NON_OPERATING_EXPENSE = {'asset_purchase', 'p2p_escrow', 'new_life'}
NON_OPERATING_INCOME = {'asset_sale', 'loan_disbursement', 'starting_balance',
                        'refund', 'p2p_escrow', 'liability_sale', 'new_life'}

# How long before the same trigger can fire again for the same player.
DEFAULT_COOLDOWN_DAYS = 7
TRIGGER_COOLDOWN_DAYS = {
    'inactivity': 7,  # the inactive-users monitor also pings; don't double up
    'negative_cash_flow': 5,
    'high_debt_to_income': 5,
    'financial_stress': 5,
    'stagnant_income': 30,
    'consistent_progress': 30,
    'single_income_source': 14,
    'low_passive_income': 14,
}
# Celebrations that only make sense once per player, ever.
ONE_TIME_TRIGGERS = {'milestone_10k', 'first_asset', 'debt_free'}

# mentor_messages.cta_action -> app route (see adulting/Adulting/lib/mentorRoutes.ts)
CTA_ROUTES = {
    'navigate_to_marketplace': '/(tabs)/investments',
    'navigate_to_jobs': '/(tabs)/jobs',
    'navigate_to_loans': '/banking',
    'navigate_to_liabilities': '/upgrade-lifestyle',
    # '/dashboard' is the app's Bank screen: cash, assets, debts and sanity in one place.
    'navigate_to_dashboard': '/dashboard',
    'navigate_to_profile': '/dashboard',     # the templates mean "your numbers", not the public profile
    'share_milestone': '/profile',           # showing off is what the profile is for
}
# Triggers with a better home than their template's general one.
TRIGGER_ROUTES = {
    'poor_credit_score': '/banking',         # the credit score lives in The Bank
    'overworking': '/(tabs)/jobs',           # "Review Schedule": the jobs and gigs
}


class _TemplateFormatter(string.Formatter):
    """str.format that fails loudly per-message instead of crashing the job."""

    def get_value(self, key, args, kwargs):
        if isinstance(key, str) and key not in kwargs:
            raise KeyError(key)
        return super().get_value(key, args, kwargs)


_formatter = _TemplateFormatter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Treat naive datetimes from the DB as UTC so subtraction never raises."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class MentorService:
    """Analyzes player finances and produces mentor advice."""

    # ------------------------------------------------------------------ metrics

    @staticmethod
    def analyze_player_finances(player_id: uuid.UUID) -> Dict:
        """Snapshot of the player's finances. Empty dict if the profile doesn't exist."""
        from app.models.asset import Asset
        from app.models.job import Job
        from app.models.player_liability import PlayerLiability
        from app.models.transaction import Transaction

        profile = Profile.query.filter_by(user_id=player_id).first()
        if not profile:
            return {}

        now = _utcnow()

        # Holdings
        assets = UserAsset.query.filter_by(user_id=player_id).all()
        total_assets = sum(float(a.value or 0) for a in assets)
        asset_count = len(assets)
        asset_types: Dict[str, float] = {}
        for a in assets:
            asset_types[a.asset_type] = asset_types.get(a.asset_type, 0) + float(a.value or 0)
        # Concentration only means something once there's a portfolio to diversify.
        max_concentration = (max(asset_types.values()) / total_assets) if (total_assets > 0 and asset_count >= 3) else 0
        total_cost_basis = sum(float(a.purchase_price or 0) * float(a.quantity or 1) for a in assets)
        asset_growth_percentage = ((total_assets - total_cost_basis) / total_cost_basis) if total_cost_basis > 0 else 0

        # Passive income = per-unit monthly yield from the catalogue × units held
        passive_income = 0.0
        if assets:
            names = {a.name for a in assets}
            catalogue = {row.name: float(row.monthly_income or 0)
                         for row in Asset.query.filter(Asset.name.in_(names)).all()}
            passive_income = sum(catalogue.get(a.name, 0.0) * float(a.quantity or 1) for a in assets)

        # Lifestyle items owned outright (resale value)
        lifestyle_value = sum(
            float(i.current_value if i.current_value is not None else i.purchase_price or 0)
            for i in PlayerLiability.query.filter_by(player_id=player_id, is_active=True).all()
        )

        # Debt actually owed (not original principal)
        debts = Liability.query.filter(Liability.user_id == player_id,
                                       Liability.remaining_balance > 0).all()
        total_debt = sum(float(d.remaining_balance or 0) for d in debts)
        total_monthly_debt = sum(float(d.monthly_payment or 0) for d in debts)

        balance = UserBalance.query.filter_by(user_id=player_id).first()
        cash = float(balance.current_balance) if balance else 0.0

        net_worth = float(profile.net_worth or 0)
        monthly_income = float(profile.monthly_income or 0)

        investable = cash + total_assets
        cash_ratio = cash / investable if investable > 0 else 0
        debt_to_income = total_monthly_debt / monthly_income if monthly_income > 0 else 0
        passive_income_ratio = passive_income / monthly_income if monthly_income > 0 else 0

        # Jobs
        current_jobs = Job.query.filter_by(user_id=player_id, is_current=True).all()
        income_stagnant_months = 0
        work_hours_per_week = 0
        if current_jobs:
            oldest_start = min(_aware(j.start_date) for j in current_jobs if j.start_date)
            months_in_job = (now - oldest_start).days / 30
            income_stagnant_months = int(months_in_job) if months_in_job >= 6 else 0
            work_hours_per_week = max(j.work_hours_per_week or 40 for j in current_jobs)
        income_sources_count = len(current_jobs) + (1 if passive_income > 0 else 0)

        # Operating cash flow over the last 30 days
        since = now - timedelta(days=30)
        rows = db.session.query(Transaction.type, Transaction.category, func.sum(Transaction.amount)) \
            .filter(Transaction.user_id == player_id, Transaction.transaction_date >= since) \
            .group_by(Transaction.type, Transaction.category).all()
        total_expenses = sum(float(total or 0) for t, cat, total in rows
                             if t == 'expense' and cat not in NON_OPERATING_EXPENSE)
        total_income_actual = sum(float(total or 0) for t, cat, total in rows
                                  if t == 'income' and cat not in NON_OPERATING_INCOME)
        cash_flow = total_income_actual - total_expenses
        expense_ratio = total_expenses / monthly_income if monthly_income > 0 else 0
        monthly_savings = max(cash_flow, 0.0)
        savings_rate = monthly_savings / monthly_income if monthly_income > 0 else 0

        had_debt = db.session.query(Transaction.id).filter(
            Transaction.user_id == player_id,
            Transaction.category.in_(('loan_disbursement', 'loan_payment')),
        ).first() is not None

        # Activity (last_active_at is bumped by the app; updated_at changes on
        # every balance sync, so it can't measure inactivity)
        last_active = _aware(profile.last_active_at) or _aware(profile.created_at) or now
        days_inactive = max(0, (now - last_active).days)
        account_age_days = (now - _aware(profile.created_at)).days if profile.created_at else 0

        return {
            'net_worth': net_worth,
            'total_assets': total_assets,
            'lifestyle_value': lifestyle_value,
            'total_liabilities': total_debt,
            'cash': cash,
            'cash_ratio': cash_ratio,
            'monthly_income': monthly_income,
            'monthly_debt_payments': total_monthly_debt,
            'debt_to_income_ratio': debt_to_income,
            'asset_concentration': max_concentration,
            'asset_types': asset_types,
            'credit_score': profile.credit_score if profile.credit_score is not None else 650,
            'asset_growth_percentage': asset_growth_percentage,
            'passive_income': passive_income,
            'passive_income_ratio': passive_income_ratio,
            'asset_count': asset_count,
            'is_first_asset': asset_count == 1,
            'income_stagnant_months': income_stagnant_months,
            'total_expenses': total_expenses,
            'expense_ratio': expense_ratio,
            'cash_flow': cash_flow,
            'had_debt': had_debt,
            'days_inactive': days_inactive,
            'account_age_months': account_age_days / 30,
            'income_sources_count': income_sources_count,
            'monthly_savings': monthly_savings,
            'savings_rate': savings_rate,
            'engagement_days': account_age_days,
            'work_hours_per_week': work_hours_per_week,
            'sanity': profile.sanity,
        }

    # ----------------------------------------------------------------- triggers

    @staticmethod
    def check_triggers(player_id: uuid.UUID, metrics: Dict) -> List[Dict]:
        """Every trigger whose condition currently holds (cooldowns applied later)."""
        triggers: List[Dict] = []

        def add(trigger_type, role, priority, **data):
            triggers.append({'type': trigger_type, 'mentor_role': role, 'priority': priority, 'data': data})

        cash = metrics.get('cash', 0)
        net_worth = metrics.get('net_worth', 0)
        monthly_income = metrics.get('monthly_income', 0)
        total_assets = metrics.get('total_assets', 0)
        total_debt = metrics.get('total_liabilities', 0)
        dti = metrics.get('debt_to_income_ratio', 0)

        # ---------------- Coach Chen (strategic)
        if metrics.get('cash_ratio', 0) > 0.5 and cash >= 1000:
            add('high_cash_ratio', 'strategic', 4,
                cash_amount=int(cash),
                cash_percentage=int(metrics['cash_ratio'] * 100),
                inflation_loss=int(cash * 0.03))

        if metrics.get('asset_concentration', 0) > 0.7:
            add('poor_diversification', 'strategic', 4,
                concentration=int(metrics['asset_concentration'] * 100))

        # Everything the player owns (cash + investments + resale value of items)
        everything_owned = cash + total_assets + metrics.get('lifestyle_value', 0)
        if total_debt > 0 and everything_owned > 0 and total_debt / everything_owned > 0.4:
            add('overextension', 'strategic', 5,
                liability_percentage=int(total_debt / everything_owned * 100))

        # "Expenses" = actual operating spending, not income.
        monthly_spend = max(metrics.get('total_expenses', 0), metrics.get('monthly_debt_payments', 0))
        if monthly_spend > 0 and cash / monthly_spend < 3:
            add('low_emergency_fund', 'strategic', 5,
                emergency_months=round(cash / monthly_spend, 1),
                cash_amount=int(cash),
                monthly_expenses=int(monthly_spend))

        if metrics.get('asset_growth_percentage', 0) > 0.15:
            add('strong_asset_growth', 'strategic', 3,
                growth_percentage=int(metrics['asset_growth_percentage'] * 100))

        if metrics.get('income_sources_count', 0) == 1:
            add('single_income_source', 'strategic', 4, income_sources=1)

        if metrics.get('savings_rate', 0) > 0.3:
            add('high_savings_rate', 'strategic', 3,
                savings_percentage=int(metrics['savings_rate'] * 100),
                monthly_savings=int(metrics.get('monthly_savings', 0)))

        # ---------------- Tasha (risk analyst)
        if dti > 0.4:
            add('high_debt_to_income', 'risk_analyst', 5,
                debt_percentage=int(dti * 100),
                monthly_debt=int(metrics.get('monthly_debt_payments', 0)))

        if monthly_income > 0 and total_assets > 0 and metrics.get('passive_income_ratio', 0) < 0.2:
            add('low_passive_income', 'risk_analyst', 4,
                passive_income=int(metrics.get('passive_income', 0)),
                passive_percentage=int(metrics.get('passive_income_ratio', 0) * 100))

        if metrics.get('expense_ratio', 0) > 0.8:
            add('high_expense_ratio', 'risk_analyst', 4,
                expense_percentage=int(metrics['expense_ratio'] * 100),
                total_expenses=int(metrics.get('total_expenses', 0)),
                monthly_income=int(monthly_income))

        if metrics.get('cash_flow', 0) < 0:
            add('negative_cash_flow', 'risk_analyst', 5,
                deficit=int(abs(metrics['cash_flow'])),
                monthly_expenses=int(metrics.get('total_expenses', 0)),
                monthly_income=int(monthly_income))

        credit_score = metrics.get('credit_score', 650)
        if credit_score < 650:
            add('poor_credit_score', 'risk_analyst', 4, credit_score=credit_score)

        if total_assets == 0 and metrics.get('account_age_months', 0) >= 0.25:  # give newcomers a week
            add('no_assets', 'risk_analyst', 5, total_assets=0)

        if 0 < dti < 0.2:
            add('low_debt_ratio', 'risk_analyst', 3, debt_percentage=int(dti * 100))

        if metrics.get('income_stagnant_months', 0) >= 6:
            add('stagnant_income', 'risk_analyst', 4, months_stagnant=metrics['income_stagnant_months'])

        # ---------------- Parent (emotional)
        if 10000 <= net_worth < 15000:
            add('milestone_10k', 'emotional', 3, net_worth=int(net_worth))

        if metrics.get('days_inactive', 0) >= 7:
            add('inactivity', 'emotional', 3, days_inactive=metrics['days_inactive'])

        if net_worth < 0:
            add('financial_stress', 'emotional', 4, net_worth=int(net_worth))

        if metrics.get('is_first_asset'):
            add('first_asset', 'emotional', 3, asset_count=1)

        if metrics.get('engagement_days', 0) >= 180 and metrics.get('days_inactive', 0) < 7:
            add('consistent_progress', 'emotional', 3, months_active=int(metrics['engagement_days'] / 30))

        # Only a real "debt free" moment if they actually had debt before.
        if metrics.get('had_debt') and total_debt == 0:
            add('debt_free', 'emotional', 2, total_debt=0)

        if metrics.get('work_hours_per_week', 0) >= 60:
            add('overworking', 'emotional', 3, hours_per_week=metrics['work_hours_per_week'])

        return triggers

    @staticmethod
    def pick_daily_triggers(player_id: uuid.UUID, triggers: Iterable[Dict], max_messages: int = 2) -> List[Dict]:
        """
        Highest-priority triggers that aren't on cooldown, at most one per mentor.
        (Before this, the same top-2 nags were pushed to every player every day.)
        """
        now = _utcnow()
        last_sent = dict(
            db.session.query(PlayerMentorInteraction.trigger_type, func.max(PlayerMentorInteraction.sent_at))
            .filter(PlayerMentorInteraction.player_id == player_id)
            .group_by(PlayerMentorInteraction.trigger_type).all()
        )

        picked: List[Dict] = []
        used_roles = set()
        for trig in sorted(triggers, key=lambda t: t['priority'], reverse=True):
            if trig['mentor_role'] in used_roles:
                continue
            sent_at = _aware(last_sent.get(trig['type']))
            if sent_at is not None:
                if trig['type'] in ONE_TIME_TRIGGERS:
                    continue
                cooldown = TRIGGER_COOLDOWN_DAYS.get(trig['type'], DEFAULT_COOLDOWN_DAYS)
                if now - sent_at < timedelta(days=cooldown):
                    continue
            picked.append(trig)
            used_roles.add(trig['mentor_role'])
            if len(picked) >= max_messages:
                break
        return picked

    # ----------------------------------------------------------------- messages

    @staticmethod
    def generate_personalized_message(player_id: uuid.UUID, trigger: Dict, username: str) -> Optional[Dict]:
        """Fill the matching mentor_messages template. None if no template or it can't be filled."""
        mentor = Mentor.query.filter_by(role=trigger['mentor_role']).first()
        if not mentor:
            logger.warning("No mentor with role %s", trigger['mentor_role'])
            return None

        message_template = MentorMessage.query.filter_by(
            mentor_id=mentor.id,
            trigger_type=trigger['type'],
            is_active=True,
        ).order_by(MentorMessage.priority.desc()).first()
        if not message_template:
            logger.info("No active template for trigger %s", trigger['type'])
            return None

        try:
            personalized = _formatter.format(message_template.message_template,
                                             username=username, **trigger['data'])
        except (KeyError, ValueError, IndexError) as e:
            logger.error("Template %s for %s could not be filled: %r", message_template.id, trigger['type'], e)
            return None

        return {
            'mentor': mentor,
            'message_template': message_template,
            'personalized_message': personalized,
            'trigger_data': trigger['data'],
        }

    @staticmethod
    def send_mentor_message(player_id: uuid.UUID, mentor_data: Dict, metrics: Dict, supabase_client=None):
        """
        Store a mentor interaction and push it to the player.

        mentor_data comes from generate_personalized_message() (template format:
        'message_template' + 'personalized_message') or from a caller that
        passes a ready 'message' (+ optional 'trigger_type').
        """
        mentor = mentor_data.get('mentor')
        if not mentor:
            return None

        message_template = mentor_data.get('message_template')
        if message_template is not None:
            message_content = mentor_data.get('personalized_message')
            trigger_type = message_template.trigger_type
        else:
            message_content = mentor_data.get('message')
            trigger_type = mentor_data.get('trigger_type', 'real_time_trigger')
        if not message_content:
            return None

        ai_metadata = dict(mentor_data.get('ai_metadata') or {})
        # Surface the template's call-to-action as a tappable button in the chat.
        if message_template is not None and message_template.cta_text and 'suggested_actions' not in ai_metadata:
            ai_metadata['suggested_actions'] = [{
                'label': message_template.cta_text,
                'screen': TRIGGER_ROUTES.get(message_template.trigger_type) or CTA_ROUTES.get(message_template.cta_action or '', '/dashboard'),
                'params': {},
            }]

        is_player_message = mentor_data.get('is_player_message', False)

        interaction = PlayerMentorInteraction(
            player_id=player_id,
            mentor_id=mentor.id,
            message_id=message_template.id if message_template is not None else None,
            message_content=message_content,
            trigger_type=trigger_type,
            player_data_snapshot=metrics or {},
            is_player_message=is_player_message,
            parent_interaction_id=mentor_data.get('parent_interaction_id'),
            ai_metadata=ai_metadata,
        )
        db.session.add(interaction)
        db.session.commit()

        if not is_player_message:
            try:
                if supabase_client is None:
                    from app import supabase as supabase_client
                from app.services.push_notification_service import ExpoPushService

                ExpoPushService.send_notification_to_user(
                    supabase_client=supabase_client,
                    user_id=str(player_id),
                    title=f'💬 {mentor.name} sent you a message',
                    body=message_content[:100] + ('...' if len(message_content) > 100 else ''),
                    notification_type='mentor_message',
                    data={
                        'type': 'mentor',
                        'interaction_id': str(interaction.id),
                        'mentorId': str(mentor.id),
                        'mentor_name': mentor.name,
                        'trigger_type': trigger_type,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send mentor message push notification: {e}")

        return interaction

    @staticmethod
    def mark_advice_followed(interaction_id: uuid.UUID, player_id: uuid.UUID, points: int = 10):
        """
        Mark a mentor message's advice as followed and award XP exactly once.
        Returns the updated interaction, or None if it doesn't exist, isn't the
        player's, is the player's own message, or was already claimed.
        """
        table = PlayerMentorInteraction.__table__
        claimed = db.session.execute(
            table.update()
            .where(table.c.id == interaction_id)
            .where(table.c.player_id == player_id)
            .where(table.c.is_player_message.is_(False))
            .where(table.c.action_taken.is_(False))
            .values(action_taken=True,
                    action_taken_at=_utcnow(),
                    points_earned=points,
                    relationship_score=func.coalesce(table.c.relationship_score, 0) + points)
            .returning(table.c.id)
        ).first()
        if not claimed:
            db.session.rollback()
            return None

        Profile.query.filter_by(user_id=player_id).update(
            {Profile.experience_points: func.coalesce(Profile.experience_points, 0) + points},
            synchronize_session=False,
        )
        db.session.commit()
        return PlayerMentorInteraction.query.get(interaction_id)

    @staticmethod
    def get_player_mentor_stats(player_id: uuid.UUID) -> Dict:
        """Aggregate stats over the mentors' messages (the player's own chat lines excluded)."""
        interactions = PlayerMentorInteraction.query.filter_by(player_id=player_id, is_player_message=False).all()

        total_messages = len(interactions)
        messages_read = sum(1 for i in interactions if i.read_at)
        advice_followed = sum(1 for i in interactions if i.action_taken)
        total_points = sum(i.points_earned or 0 for i in interactions)

        mentor_scores: Dict[str, int] = {}
        for i in interactions:
            key = str(i.mentor_id)
            mentor_scores[key] = mentor_scores.get(key, 0) + (i.relationship_score or 0)

        return {
            'total_messages': total_messages,
            'messages_read': messages_read,
            'advice_followed': advice_followed,
            'total_points': total_points,
            'mentor_scores': mentor_scores,
            'engagement_rate': messages_read / total_messages if total_messages else 0,
            'action_rate': advice_followed / total_messages if total_messages else 0,
        }

    @staticmethod
    def check_real_time_triggers(player_id: uuid.UUID, action: str, action_data: Dict) -> Optional[Dict]:
        """
        Real-time reactions to player actions are intentionally disabled in favour
        of the AI chat. Callers (asset/liability/loan/education routes) still call
        this so it can be re-enabled in one place.
        """
        return None
