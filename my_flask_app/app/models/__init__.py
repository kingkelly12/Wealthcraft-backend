# Import all 37 models so Flask-Migrate can detect them
from app.models.user import User
from app.models.profile import Profile
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction
from app.models.user_asset import UserAsset
from app.models.asset import Asset
from app.models.job import Job
from app.models.course import Course
from app.models.rental_property import RentalProperty
from app.models.p2p_loan import P2PLoan
from app.models.bank_loan import BankLoan
from app.models.liability import Liability
from app.models.liability_item import LiabilityItem
from app.models.notification import Notification
from app.models.player_rental import PlayerRental
from app.models.user_follow import UserFollow
from app.models.chat_message import ChatMessage
from app.models.life_event import LifeEvent
from app.models.integrated_mission import IntegratedMission
from app.models.player_mission_progress import PlayerMissionProgress
from app.models.loan_repayment import LoanRepayment
from app.models.job_market import JobMarket
from app.models.user_course import UserCourse
from app.models.life_event_choice import LifeEventChoice
from app.models.user_life_event import UserLifeEvent
from app.models.monthly_deduction import MonthlyDeduction
from app.models.player_liability import PlayerLiability
from app.models.mission_decision_point import MissionDecisionPoint
from app.models.mission_decision_option import MissionDecisionOption
from app.models.mission_success_criteria import MissionSuccessCriteria
from app.models.integrated_mission_event import IntegratedMissionEvent
from app.models.mission_event_choice import MissionEventChoice
from app.models.player_mission_decision import PlayerMissionDecision
from app.models.player_mission_success_tracking import PlayerMissionSuccessTracking
from app.models.mission_completion_result import MissionCompletionResult
from app.models.mission_story_event import MissionStoryEvent
from app.models.player_story_progress import PlayerStoryProgress
from app.models.mission_course import MissionCourse
from app.models.mission_asset import MissionAsset
from app.models.mentor import Mentor
from app.models.mentor_message import MentorMessage
from app.models.player_mentor_interaction import PlayerMentorInteraction

__all__ = [
    'User',
    'Profile',
    'UserBalance',
    'Transaction',
    'UserAsset',
    'Asset',
    'Job',
    'Course',
    'RentalProperty',
    'P2PLoan',
    'BankLoan',
    'Liability',
    'LiabilityItem',
    'Notification',
    'PlayerRental',
    'UserFollow',
    'ChatMessage',
    'LifeEvent',
    'IntegratedMission',
    'PlayerMissionProgress',
    'LoanRepayment',
    'JobMarket',
    'UserCourse',
    'FamilyMember',
    'LifeEventChoice',
    'UserLifeEvent',
    'MonthlyDeduction',
    'PlayerLiability',
    'MissionDecisionPoint',
    'MissionDecisionOption',
    'MissionSuccessCriteria',
    'IntegratedMissionEvent',
    'MissionEventChoice',
    'PlayerMissionDecision',
    'PlayerMissionSuccessTracking',
    'MissionCompletionResult',
    'MissionStoryEvent',
    'PlayerStoryProgress',
    'MissionCourse',
    'MissionAsset',
    'Mentor',
    'MentorMessage',
    'PlayerMentorInteraction'
]
