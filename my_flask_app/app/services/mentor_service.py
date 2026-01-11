from app import db
from app.models.mentor import Mentor
from app.models.mentor_message import MentorMessage
from app.models.player_mentor_interaction import PlayerMentorInteraction
from app.models.profile import Profile
from app.models.user_asset import UserAsset
from app.models.liability import Liability
from app.models.user_balance import UserBalance
from typing import Dict, List, Optional
import uuid
from datetime import datetime, timedelta

class MentorService:
    """Service for analyzing player financial data and generating mentor advice"""

    @staticmethod
    def analyze_player_finances(player_id: uuid.UUID) -> Dict:
        """Analyze player's financial situation and return metrics"""
        from app.models.transaction import Transaction
        from app.models.job import Job
        from datetime import timedelta
        
        # Get profile
        profile = Profile.query.filter_by(user_id=player_id).first()
        if not profile:
            return {}

        # Get assets
        assets = UserAsset.query.filter_by(user_id=player_id).all()
        total_assets = sum([float(asset.value) for asset in assets])
        
        # Get liabilities
        liabilities = Liability.query.filter_by(user_id=player_id).all()
        total_liabilities = sum([float(liability.amount) for liability in liabilities])
        total_monthly_debt = sum([float(liability.monthly_payment) for liability in liabilities])

        # Get balance
        balance = UserBalance.query.filter_by(user_id=player_id).first()
        cash = float(balance.current_balance) if balance else 0

        # Calculate metrics
        net_worth = float(profile.net_worth) if profile.net_worth else 0
        monthly_income = float(profile.monthly_income) if profile.monthly_income else 0
        
        # Asset diversification
        asset_types = {}
        for asset in assets:
            asset_type = asset.asset_type
            asset_types[asset_type] = asset_types.get(asset_type, 0) + float(asset.value)

        max_concentration = max(asset_types.values()) / total_assets if total_assets > 0 else 0

        # Calculate ratios
        cash_ratio = cash / total_assets if total_assets > 0 else 0
        debt_to_income = total_monthly_debt / monthly_income if monthly_income > 0 else 0
        
        # === NEW METRICS USING EXISTING DATA ===
        
        # 1. Asset growth (compare purchase price vs current value)
        total_purchase_price = sum([float(asset.purchase_price or 0) for asset in assets])
        asset_growth_percentage = ((total_assets - total_purchase_price) / total_purchase_price) if total_purchase_price > 0 else 0
        
        # 2. Passive income (from assets with monthly_income)
        # Note: Assuming assets table has monthly_income field, otherwise calculate from dividends
        passive_income = 0  # Placeholder - would need asset income tracking
        passive_income_ratio = passive_income / monthly_income if monthly_income > 0 else 0
        
        # 3. First asset check
        asset_count = len(assets)
        first_asset_date = min([asset.purchase_date for asset in assets]) if assets else None
        is_first_asset = asset_count == 1 if first_asset_date else False
        
        # 4. Income stagnation (check job history)
        current_jobs = Job.query.filter_by(user_id=player_id, is_current=True).all()
        income_stagnant_months = 0
        if current_jobs:
            oldest_job = min(current_jobs, key=lambda j: j.start_date)
            months_in_job = (datetime.utcnow() - oldest_job.start_date).days / 30
            # If same job for 6+ months with no salary change, it's stagnant
            income_stagnant_months = int(months_in_job) if months_in_job >= 6 else 0
        
        # 5. Expense ratio (from transactions in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_expenses = Transaction.query.filter(
            Transaction.user_id == player_id,
            Transaction.type == 'expense',
            Transaction.transaction_date >= thirty_days_ago
        ).all()
        total_expenses = sum([float(t.amount) for t in recent_expenses])
        expense_ratio = total_expenses / monthly_income if monthly_income > 0 else 0
        
        # 6. Cash flow (income - expenses)
        recent_income = Transaction.query.filter(
            Transaction.user_id == player_id,
            Transaction.type == 'income',
            Transaction.transaction_date >= thirty_days_ago
        ).all()
        total_income_actual = sum([float(t.amount) for t in recent_income])
        cash_flow = total_income_actual - total_expenses
        
        # 7. Inactivity (days since last update)
        days_inactive = (datetime.utcnow() - profile.updated_at).days if profile.updated_at else 0
        
        # 8. Account age (for consistent progress tracking)
        account_age_months = (datetime.utcnow() - profile.created_at).days / 30 if profile.created_at else 0
        
        # === NEW METRICS FROM DATABASE FIELDS ===
        
        # 9. Income sources count (from profile)
        income_sources_count = profile.income_sources_count if profile else 1
        
        # 10. Monthly savings (from profile)
        monthly_savings = float(profile.monthly_savings) if profile and profile.monthly_savings else 0
        savings_rate = monthly_savings / monthly_income if monthly_income > 0 else 0
        
        # 11. Engagement days (from profile)
        engagement_days = profile.engagement_days if profile else 0
        
        # 12. Work hours (from current job)
        work_hours_per_week = 0
        if current_jobs:
            work_hours_per_week = max([job.work_hours_per_week or 40 for job in current_jobs])
        
        # 13. Net worth growth (from financial snapshots)
        from app.models.player_financial_snapshot import PlayerFinancialSnapshot
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        old_snapshot = PlayerFinancialSnapshot.query.filter(
            PlayerFinancialSnapshot.player_id == player_id,
            PlayerFinancialSnapshot.snapshot_date <= thirty_days_ago
        ).order_by(PlayerFinancialSnapshot.snapshot_date.desc()).first()
        
        net_worth_growth_percentage = 0
        if old_snapshot and old_snapshot.net_worth != 0:
            net_worth_growth_percentage = (net_worth - float(old_snapshot.net_worth)) / float(old_snapshot.net_worth)
        
        return {
            'net_worth': net_worth,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'cash': cash,
            'cash_ratio': cash_ratio,
            'monthly_income': monthly_income,
            'monthly_debt_payments': total_monthly_debt,
            'debt_to_income_ratio': debt_to_income,
            'asset_concentration': max_concentration,
            'asset_types': asset_types,
            'credit_score': profile.credit_score if profile else 650,
            'asset_growth_percentage': asset_growth_percentage,
            'passive_income': passive_income,
            'passive_income_ratio': passive_income_ratio,
            'asset_count': asset_count,
            'is_first_asset': is_first_asset,
            'income_stagnant_months': income_stagnant_months,
            'total_expenses': total_expenses,
            'expense_ratio': expense_ratio,
            'cash_flow': cash_flow,
            'days_inactive': days_inactive,
            'account_age_months': account_age_months,
            'income_sources_count': income_sources_count,
            'monthly_savings': monthly_savings,
            'savings_rate': savings_rate,
            'engagement_days': engagement_days,
            'work_hours_per_week': work_hours_per_week,
            'net_worth_growth_percentage': net_worth_growth_percentage
        }

    @staticmethod
    def check_triggers(player_id: uuid.UUID, metrics: Dict) -> List[Dict]:
        """Check which mentor messages should be triggered"""
        triggers = []

        # ============================================
        # COACH CHEN TRIGGERS (Strategic)
        # ============================================
        
        # 1. High cash ratio (>50%)
        if metrics.get('cash_ratio', 0) > 0.5:
            triggers.append({
                'type': 'high_cash_ratio',
                'mentor_role': 'strategic',
                'priority': 4,
                'data': {
                    'cash_amount': metrics['cash'],
                    'cash_percentage': int(metrics['cash_ratio'] * 100),
                    'inflation_loss': int(metrics['cash'] * 0.03)
                }
            })

        # 2. Poor diversification (>70% in one asset)
        if metrics.get('asset_concentration', 0) > 0.7:
            triggers.append({
                'type': 'poor_diversification',
                'mentor_role': 'strategic',
                'priority': 4,
                'data': {'concentration': int(metrics['asset_concentration'] * 100)}
            })

        # 3. Net worth growth (>20% increase) ✅ NOW ACTIVE
        if metrics.get('net_worth_growth_percentage', 0) > 0.2:
            triggers.append({
                'type': 'net_worth_growth',
                'mentor_role': 'strategic',
                'priority': 3,
                'data': {'growth_percentage': int(metrics['net_worth_growth_percentage'] * 100)}
            })
        
        # 4. Overextension (>40% liabilities ratio)
        total_assets = metrics.get('total_assets', 0)
        total_liabilities = metrics.get('total_liabilities', 0)
        if total_assets > 0:
            liability_ratio = total_liabilities / total_assets
            if liability_ratio > 0.4:
                triggers.append({
                    'type': 'overextension',
                    'mentor_role': 'strategic',
                    'priority': 5,
                    'data': {'liability_percentage': int(liability_ratio * 100)}
                })

        # 5. Low emergency fund (<3 months expenses)
        monthly_income = metrics.get('monthly_income', 0)
        cash = metrics.get('cash', 0)
        if monthly_income > 0:
            emergency_months = cash / monthly_income
            if emergency_months < 3:
                triggers.append({
                    'type': 'low_emergency_fund',
                    'mentor_role': 'strategic',
                    'priority': 5,
                    'data': {
                        'emergency_months': round(emergency_months, 1),
                        'cash_amount': cash,
                        'monthly_expenses': monthly_income
                    }
                })

        # 6. Strong asset growth (>15% growth) ✅ NOW ACTIVE
        if metrics.get('asset_growth_percentage', 0) > 0.15:
            triggers.append({
                'type': 'strong_asset_growth',
                'mentor_role': 'strategic',
                'priority': 3,
                'data': {'growth_percentage': int(metrics['asset_growth_percentage'] * 100)}
            })
        
        # 7. Single income source ✅ NOW ACTIVE
        if metrics.get('income_sources_count', 1) == 1:
            triggers.append({
                'type': 'single_income_source',
                'mentor_role': 'strategic',
                'priority': 4,
                'data': {'income_sources': 1}
            })
        
        # 8. High savings rate (>30%) ✅ NOW ACTIVE
        if metrics.get('savings_rate', 0) > 0.3:
            triggers.append({
                'type': 'high_savings_rate',
                'mentor_role': 'strategic',
                'priority': 3,
                'data': {
                    'savings_percentage': int(metrics['savings_rate'] * 100),
                    'monthly_savings': metrics['monthly_savings']
                }
            })

        # ============================================
        # TASHA TRIGGERS (Risk Analyst)
        # ============================================

        # 1. High debt-to-income (>40%)
        if metrics.get('debt_to_income_ratio', 0) > 0.4:
            triggers.append({
                'type': 'high_debt_to_income',
                'mentor_role': 'risk_analyst',
                'priority': 5,
                'data': {
                    'debt_percentage': int(metrics['debt_to_income_ratio'] * 100),
                    'monthly_debt': metrics['monthly_debt_payments']
                }
            })

        # 2. Low passive income (<20% of total) ✅ NOW ACTIVE
        if metrics.get('passive_income_ratio', 0) < 0.2 and metrics.get('monthly_income', 0) > 0:
            triggers.append({
                'type': 'low_passive_income',
                'mentor_role': 'risk_analyst',
                'priority': 4,
                'data': {
                    'passive_income': metrics['passive_income'],
                    'passive_percentage': int(metrics['passive_income_ratio'] * 100)
                }
            })

        # 3. High expense ratio (>80%) ✅ NOW ACTIVE
        if metrics.get('expense_ratio', 0) > 0.8:
            triggers.append({
                'type': 'high_expense_ratio',
                'mentor_role': 'risk_analyst',
                'priority': 4,
                'data': {
                    'expense_percentage': int(metrics['expense_ratio'] * 100),
                    'total_expenses': metrics['total_expenses'],
                    'monthly_income': metrics['monthly_income']
                }
            })

        # 4. Negative cash flow ✅ NOW ACTIVE
        if metrics.get('cash_flow', 0) < 0:
            triggers.append({
                'type': 'negative_cash_flow',
                'mentor_role': 'risk_analyst',
                'priority': 5,
                'data': {
                    'deficit': abs(metrics['cash_flow']),
                    'monthly_expenses': metrics['total_expenses'],
                    'monthly_income': metrics['monthly_income']
                }
            })

        # 5. Poor credit score (<650)
        credit_score = metrics.get('credit_score', 650)
        if credit_score < 650:
            triggers.append({
                'type': 'poor_credit_score',
                'mentor_role': 'risk_analyst',
                'priority': 4,
                'data': {'credit_score': credit_score}
            })

        # 6. No assets (total_assets = 0)
        if metrics.get('total_assets', 0) == 0:
            triggers.append({
                'type': 'no_assets',
                'mentor_role': 'risk_analyst',
                'priority': 5,
                'data': {'total_assets': 0}
            })

        # 7. Excellent debt management (<20% debt-to-income)
        if 0 < metrics.get('debt_to_income_ratio', 0) < 0.2:
            triggers.append({
                'type': 'low_debt_ratio',
                'mentor_role': 'risk_analyst',
                'priority': 3,
                'data': {'debt_percentage': int(metrics['debt_to_income_ratio'] * 100)}
            })

        # 8. Stagnant income ✅ NOW ACTIVE
        if metrics.get('income_stagnant_months', 0) >= 6:
            triggers.append({
                'type': 'stagnant_income',
                'mentor_role': 'risk_analyst',
                'priority': 4,
                'data': {'months_stagnant': metrics['income_stagnant_months']}
            })

        # ============================================
        # PARENT TRIGGERS (Emotional)
        # ============================================

        # 1. First $10K milestone
        net_worth = metrics.get('net_worth', 0)
        if net_worth >= 10000 and net_worth < 15000:
            triggers.append({
                'type': 'milestone_10k',
                'mentor_role': 'emotional',
                'priority': 3,
                'data': {'net_worth': net_worth}
            })

        # 2. Expensive purchase - handled by real-time triggers
        
        # 3. Inactivity ✅ NOW ACTIVE
        if metrics.get('days_inactive', 0) >= 7:
            triggers.append({
                'type': 'inactivity',
                'mentor_role': 'emotional',
                'priority': 3,
                'data': {'days_inactive': metrics['days_inactive']}
            })

        # 4. Financial stress (negative net worth)
        if net_worth < 0:
            triggers.append({
                'type': 'financial_stress',
                'mentor_role': 'emotional',
                'priority': 4,
                'data': {'net_worth': net_worth}
            })

        # 5. First asset purchase ✅ NOW ACTIVE
        if metrics.get('is_first_asset', False):
            triggers.append({
                'type': 'first_asset',
                'mentor_role': 'emotional',
                'priority': 3,
                'data': {'asset_count': 1}
            })

        # 6. Consistent progress ✅ NOW ACTIVE
        if metrics.get('engagement_days', 0) >= 180:  # 6 months
            triggers.append({
                'type': 'consistent_progress',
                'mentor_role': 'emotional',
                'priority': 3,
                'data': {'months_active': int(metrics['engagement_days'] / 30)}
            })

        # 7. Debt freedom (zero debt after having debt) - would need debt history
        if metrics.get('total_liabilities', 0) == 0 and metrics.get('total_assets', 0) > 0:
            triggers.append({
                'type': 'debt_free',
                'mentor_role': 'emotional',
                'priority': 2,
                'data': {'total_debt': 0}
            })

        # 8. Overworking ✅ NOW ACTIVE
        if metrics.get('work_hours_per_week', 0) >= 60:
            triggers.append({
                'type': 'overworking',
                'mentor_role': 'emotional',
                'priority': 3,
                'data': {'hours_per_week': metrics['work_hours_per_week']}
            })

        return triggers

    @staticmethod
    def generate_personalized_message(player_id: uuid.UUID, trigger: Dict, username: str) -> Optional[Dict]:
        """Generate a personalized mentor message"""
        
        # Get mentor by role
        mentor = Mentor.query.filter_by(role=trigger['mentor_role']).first()
        if not mentor:
            return None

        # Get message template
        message_template = MentorMessage.query.filter_by(
            mentor_id=mentor.id,
            trigger_type=trigger['type'],
            is_active=True
        ).first()

        if not message_template:
            return None

        # Personalize message
        template = message_template.message_template
        personalized = template.format(
            username=username,
            **trigger['data']
        )

        return {
            'mentor': mentor,
            'message_template': message_template,
            'personalized_message': personalized,
            'trigger_data': trigger['data']
        }

    @staticmethod
    def send_mentor_message(player_id: uuid.UUID, mentor_data: Dict, metrics: Dict):
        """Create and save a mentor interaction"""
        
        interaction = PlayerMentorInteraction(
            player_id=player_id,
            mentor_id=mentor_data['mentor'].id,
            message_id=mentor_data['message_template'].id,
            message_content=mentor_data['personalized_message'],
            trigger_type=mentor_data['message_template'].trigger_type,
            player_data_snapshot=metrics
        )
        
        db.session.add(interaction)
        db.session.commit()
        
        return interaction

    @staticmethod
    def mark_advice_followed(interaction_id: uuid.UUID, points: int = 10):
        """Mark that player followed mentor advice and award points"""
        
        interaction = PlayerMentorInteraction.query.get(interaction_id)
        if not interaction:
            return None

        interaction.action_taken = True
        interaction.action_taken_at = datetime.utcnow()
        interaction.points_earned = points
        interaction.relationship_score += points

        # Update profile with earned points
        profile = Profile.query.filter_by(user_id=interaction.player_id).first()
        if profile:
            profile.experience_points = (profile.experience_points or 0) + points

        db.session.commit()
        return interaction

    @staticmethod
    def get_player_mentor_stats(player_id: uuid.UUID) -> Dict:
        """Get player's mentor relationship statistics"""
        
        interactions = PlayerMentorInteraction.query.filter_by(player_id=player_id).all()
        
        total_messages = len(interactions)
        messages_read = len([i for i in interactions if i.read_at])
        advice_followed = len([i for i in interactions if i.action_taken])
        total_points = sum([i.points_earned for i in interactions])
        
        # Get relationship scores per mentor
        mentor_scores = {}
        for interaction in interactions:
            mentor_id = str(interaction.mentor_id)
            if mentor_id not in mentor_scores:
                mentor_scores[mentor_id] = 0
            mentor_scores[mentor_id] += interaction.relationship_score

        return {
            'total_messages': total_messages,
            'messages_read': messages_read,
            'advice_followed': advice_followed,
            'total_points': total_points,
            'mentor_scores': mentor_scores,
            'engagement_rate': messages_read / total_messages if total_messages > 0 else 0,
            'action_rate': advice_followed / total_messages if total_messages > 0 else 0
        }

    @staticmethod
    def check_real_time_triggers(player_id: uuid.UUID, action: str, action_data: Dict) -> Optional[Dict]:
        """Check for immediate mentor reactions to player actions"""
        
        # Get username
        profile = Profile.query.filter_by(user_id=player_id).first()
        username = profile.username if profile else "Player"

        # Buying expensive liability (yacht, helicopter, etc.)
        if action == 'buy_liability' and action_data.get('cost', 0) > 50000:
            mentor = Mentor.query.filter_by(role='emotional').first()
            if mentor:
                message = f"Sweetheart, I saw you bought a {action_data.get('item_name')}. I know you worked hard, but remember - things don't bring lasting happiness. Financial freedom does. Are you sure this aligns with your goals?"
                return {
                    'mentor': mentor,
                    'message': message,
                    'trigger_type': 'expensive_purchase',
                    'immediate': True
                }

        # Taking on high debt
        if action == 'take_loan' and action_data.get('amount', 0) > 100000:
            mentor = Mentor.query.filter_by(role='risk_analyst').first()
            if mentor:
                message = f"Hi {username}, that's a ${action_data.get('amount'):,} loan. Let's make sure you have a solid repayment plan. High debt can become a trap if not managed carefully."
                return {
                    'mentor': mentor,
                    'message': message,
                    'trigger_type': 'high_debt_taken',
                    'immediate': True
                }

        # Selling all assets (panic selling)
        if action == 'sell_assets' and action_data.get('percentage_sold', 0) > 0.5:
            mentor = Mentor.query.filter_by(role='strategic').first()
            if mentor:
                message = f"Whoa {username}! You just sold {int(action_data.get('percentage_sold') * 100)}% of your portfolio. Panic selling is how people lose wealth. What's driving this decision?"
                return {
                    'mentor': mentor,
                    'message': message,
                    'trigger_type': 'panic_selling',
                    'immediate': True
                }

        return None
