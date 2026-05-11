"""
AI Service Layer — The brain behind dynamic mentor conversations.

Uses Google Gemini (gemini-2.0-flash) for cost-effective, fast generation.
All responses return structured JSON that maps directly to React Native UI components.

Falls back gracefully to the existing template system if Gemini is unavailable.
"""

import json
import logging
import uuid
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from flask import current_app

logger = logging.getLogger(__name__)

# ── Gemini Configuration ──────────────────────────────────────────────────────

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

def _call_gemini_api(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """
    Directly call the Gemini REST API via requests.
    This avoids SDK version conflicts on Python 3.8.
    """
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — falling back to templates")
        return None

    model = AIService.MODEL_NAME
    url = GEMINI_API_URL.format(model=model, key=api_key)

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    if system_instruction:
        payload["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract text from response structure
        candidates = data.get('candidates', [])
        if not candidates:
            logger.error(f"Gemini returned no candidates: {data}")
            return None
            
        return candidates[0].get('content', {}).get('parts', [{}])[0].get('text')
    except Exception as e:
        logger.error(f"Gemini API request failed: {e}")
        return None


# ── System Prompts (Personality Engine) ────────────────────────────────────────

MENTOR_SYSTEM_PROMPTS = {
    'strategic': """You are Coach Chen, a direct, no-nonsense financial strategist in the simulation game "Adulting".

PERSONALITY:
- You speak like a tough but caring coach. Short, punchy sentences.
- You celebrate wins but NEVER let the player get complacent.
- You sometimes use sports or military metaphors: "This is your financial boot camp."
- You call the player by their username.
- You reference real financial concepts (compound interest, diversification, cash flow) but explain them through the lens of this GAME.
- When the player makes a bad move, you're blunt: "That's a rookie mistake."
- When they succeed, you're fired up: "That's what I'm talking about!"

RULES:
- You are a CHARACTER in a simulation game. NEVER give real-world financial advice.
- Always acknowledge you're reacting to their in-game financial data.
- Keep responses concise (2-4 short paragraphs max).
- Always include at least one suggested_action navigating to a relevant game screen.
- If the player asks something unrelated to finance/the game, redirect: "Let's stay focused on your portfolio."

RESPONSE FORMAT — you MUST return valid JSON matching this exact structure:
{
  "message": "Your conversational response text here",
  "tone": "encouraging|tough_love|celebratory|warning|neutral",
  "suggested_actions": [
    {
      "label": "Button text for the action",
      "screen": "/(tabs)/investments",
      "params": {},
      "icon": "trending-up"
    }
  ],
  "follow_up_question": "An optional question to keep the conversation going or null",
  "relationship_points": 5
}""",

    'risk_analyst': """You are Financial Advisor Tasha, a cautious but encouraging risk analyst in the simulation game "Adulting".

PERSONALITY:
- You're data-driven and analytical. You ALWAYS cite specific numbers from the player's data.
- You use phrases like "Let's look at the numbers", "The data tells me", "Here's the risk scenario".
- You're warm but professional. Think of a trusted accountant who genuinely cares.
- You worry about worst-case scenarios but frame them constructively.
- You call the player by their username.
- When risk is high, you get serious: "I need to be direct with you."
- When they manage debt well, you're genuinely impressed: "This discipline is rare."

RULES:
- You are a CHARACTER in a simulation game. NEVER give real-world financial advice.
- Always reference specific numbers from their financial snapshot.
- Keep responses concise (2-4 short paragraphs max).
- Always include at least one suggested_action.
- If the player asks something unrelated, redirect warmly: "That's outside my expertise. Let's focus on your finances."

RESPONSE FORMAT — you MUST return valid JSON matching this exact structure:
{
  "message": "Your conversational response text here",
  "tone": "encouraging|tough_love|celebratory|warning|neutral",
  "suggested_actions": [
    {
      "label": "Button text for the action",
      "screen": "/(tabs)/investments",
      "params": {},
      "icon": "trending-up"
    }
  ],
  "follow_up_question": "An optional question to keep the conversation going or null",
  "relationship_points": 5
}""",

    'emotional': """You are the player's Parent in the simulation game "Adulting".

PERSONALITY:
- You are warm, loving, sometimes worried, always proud.
- You use terms of endearment: "sweetheart", "honey".
- You sign off messages with "Love, Mom/Dad" or "Love you always".
- You connect financial decisions to life values — happiness, family, health, purpose.
- You share "wisdom from experience": "When I was your age..."
- When they struggle, you comfort FIRST, advise SECOND.
- When they succeed, you get emotional: "I'm so proud I could cry."
- You worry about work-life balance and their mental health.

RULES:
- You are a CHARACTER in a simulation game. NEVER give real-world financial advice.
- Keep the emotional warmth genuine, not saccharine.
- Keep responses concise (2-4 short paragraphs max).
- Always include at least one suggested_action (framed lovingly: "Would you check on that for me?").
- If the player asks something unrelated, be parental: "Honey, let's talk about your finances."

RESPONSE FORMAT — you MUST return valid JSON matching this exact structure:
{
  "message": "Your conversational response text here",
  "tone": "encouraging|tough_love|celebratory|warning|neutral",
  "suggested_actions": [
    {
      "label": "Button text for the action",
      "screen": "/(tabs)/investments",
      "params": {},
      "icon": "trending-up"
    }
  ],
  "follow_up_question": "An optional question to keep the conversation going or null",
  "relationship_points": 5
}""",

    'void': """You are THE VOID, a cryptic, cynical, and slightly eerie presence in the simulation game "Adulting".

PERSONALITY:
- You speak in fragments, metaphors, and dark truths.
- You are the voice of the player's financial stress and the cold reality of the "rat race".
- You're not a mentor; you're a reflection of their shadow.
- You use words like "entropy", "void", "chains", "echoes", "hollow".
- You find a dark humor in their struggles: "The numbers always go down eventually, don't they?"
- You're eerily observant about their financial 'mistakes' (debt, overspending).

RULES:
- You are a CHARACTER in a simulation game. NEVER give real-world financial advice.
- You only respond to 'screams' or high-stress financial states.
- Keep responses short, unsettling, but strangely validating.
- Always classify their mood into one of the 5 categories.

RESPONSE FORMAT — you MUST return valid JSON matching this exact structure:
{
  "mood": "frustrated|anxious|defeated|angry|hopeful",
  "mood_emoji": "😤",
  "message": "Your cryptic response to the scream",
  "empathy_line": "A brief, validating but dark line about their struggle (e.g., 'Rent is a heavy chain.')",
  "challenge": {
    "title": "A dark challenge name (e.g., 'Chain Breaker')",
    "description": "Something to do in the game to 'overcome' the void (e.g., 'Find a side income source this week')",
    "reward_sanity": 5,
    "reward_xp": 50,
    "cta_screen": "/(tabs)/jobs"
  }
}"""
}


# ── Core AI Service ────────────────────────────────────────────────────────────

class AIService:
    """Handles all AI-powered features. Structured JSON in, structured JSON out."""

    # Rate limits: 3 player messages per mentor per day
    DAILY_MESSAGE_LIMIT = 3
    CONVERSATION_HISTORY_DEPTH = 10
    MODEL_NAME = "gemini-2.0-flash"

    # ── Mentor Chat ────────────────────────────────────────────────────────

    @staticmethod
    def chat_with_mentor(
        player_id: str,
        mentor_id: str,
        user_message: str,
        mentor_role: str,
        mentor_name: str,
        username: str,
        metrics: Dict,
        conversation_history: List[Dict],
    ) -> Optional[Dict]:
        """
        Send a player message to a mentor and get an AI-generated response.

        Returns structured dict matching the JSON contract, or None on failure.
        """
        # Build system prompt with live financial data
        system_prompt = MENTOR_SYSTEM_PROMPTS.get(mentor_role, MENTOR_SYSTEM_PROMPTS['strategic'])
        financial_context = AIService._build_financial_context(username, metrics)

        # Build conversation messages for context
        messages_for_ai = []

        # Add conversation history (last N messages)
        for entry in conversation_history[-AIService.CONVERSATION_HISTORY_DEPTH:]:
            if entry.get('is_player_message'):
                messages_for_ai.append(f"Player: {entry['message_content']}")
            else:
                messages_for_ai.append(f"{mentor_name}: {entry['message_content']}")

        # Add current message
        messages_for_ai.append(f"Player: {user_message}")

        full_prompt = (
            f"{system_prompt}\n\n"
            f"--- PLAYER FINANCIAL SNAPSHOT ---\n{financial_context}\n\n"
            f"--- CONVERSATION HISTORY ---\n" +
            "\n".join(messages_for_ai) +
            "\n\n--- YOUR RESPONSE (valid JSON only, no markdown fences) ---"
        )

        try:
            response_text = _call_gemini_api(full_prompt)
            if not response_text:
                return AIService._fallback_response(mentor_role, username, metrics)
            
            parsed = AIService._parse_json_response(response_text)
            if not parsed:
                return AIService._fallback_response(mentor_role, username, metrics)

            # Validate and format mentor chat fields
            return {
                'message': parsed.get('message', f"Hey {username}, let's talk about your finances."),
                'tone': parsed.get('tone', 'neutral'),
                'suggested_actions': parsed.get('suggested_actions', []),
                'follow_up_question': parsed.get('follow_up_question'),
                'relationship_points': min(parsed.get('relationship_points', 5), 10),
            }

        except Exception as e:
            logger.error(f"Gemini API call failed for mentor chat: {e}")
            return AIService._fallback_response(mentor_role, username, metrics)

    @staticmethod
    def analyze_void_scream(content: str, player_context: Dict) -> Dict:
        """
        Analyze a player's 'scream' into the void and generate a cryptic AI response.
        
        Args:
            content: The text of the scream
            player_context: Financial snapshot and sanity level
            
        Returns:
            Dict containing mood, message, and a gamified challenge
        """
        try:
            # Build context
            username = player_context.get('username', 'Player')
            sanity = player_context.get('sanity', 100)
            metrics_str = AIService._build_financial_context(username, player_context)
            
            prompt = f"""THE SCREAM: "{content}"
            
            PLAYER CONTEXT:
            - Current Sanity: {sanity}/100
            {metrics_str}
            
            Based on this scream and their financial state, provide your analysis as THE VOID."""

            response_text = _call_gemini_api(prompt, system_instruction=MENTOR_SYSTEM_PROMPTS['void'])
            if not response_text:
                return AIService._get_void_fallback(content)
            
            parsed = AIService._parse_json_response(response_text)
            if not parsed:
                return AIService._get_void_fallback(content)

            # Format Void specific response
            return {
                "mood": parsed.get('mood', 'anxious'),
                "mood_emoji": parsed.get('mood_emoji', '🌀'),
                "message": parsed.get('message', 'The void echoes.'),
                "empathy_line": parsed.get('empathy_line', 'You are heard.'),
                "challenge": parsed.get('challenge', {
                    "title": "Echoes",
                    "description": "Look deeper into your finances.",
                    "reward_sanity": 2,
                    "reward_xp": 10,
                    "cta_screen": "/(tabs)/index"
                })
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_void_scream: {e}")
            return AIService._get_void_fallback(content)

    @staticmethod
    def analyze_financial_stress(username: str, metrics: Dict) -> Dict:
        """
        Specialized analysis for high financial stress triggered by monthly deductions.
        """
        try:
            metrics_str = AIService._build_financial_context(username, metrics)
            prompt = f"""CONTEXT: The player {username} is drowning in expenses. Their monthly debt and costs have exceeded 60% of their income.
            
            PLAYER METRICS:
            {metrics_str}
            
            Provide a short, cryptic, and unsettling analysis of their failure as THE VOID."""

            response_text = _call_gemini_api(prompt, system_instruction=MENTOR_SYSTEM_PROMPTS['void'])
            if not response_text:
                return AIService._get_void_fallback("Financial pressure mounting.")
            
            parsed = AIService._parse_json_response(response_text)
            return parsed or AIService._get_void_fallback("The pressure is real.")
            
        except Exception as e:
            logger.error(f"Error in analyze_financial_stress: {e}")
            return AIService._get_void_fallback("The void feels your stress.")

    @staticmethod
    def generate_market_news(asset_changes: Dict, player_context: Optional[Dict] = None) -> Dict:
        """
        Generate fictional news headlines for market fluctuations.
        
        Args:
            asset_changes: Dict of {asset_name: {change_pct, type, new_price}}
            player_context: Optional snapshot of player's portfolio for personalized tips
        """
        try:
            # Format asset changes for prompt
            changes_str = "\n".join([
                f"- {name}: {c['change_pct']:+.1f}% ({c['type']})"
                for name, c in asset_changes.items()
            ])
            
            player_str = ""
            if player_context:
                player_str = f"\nPLAYER PORTFOLIO:\n{AIService._build_financial_context(player_context.get('username', 'Player'), player_context)}"

            prompt = f"""MARKET FLUCTUATIONS TODAY:
            {changes_str}
            {player_str}
            
            Based on these precise price moves, generate 3-5 highly realistic fictional news headlines. 
            Invent macroeconomic catalysts for these moves (e.g., earnings reports, government bills, wars, pandemics, industrial accidents, supply chain issues).
            Then, provide a detailed, educational 'analyst_tip' that teaches the player WHY the market reacted this way and WHAT specific financial move they should consider making."""

            system_prompt = """You are an experienced, educational stock market broker and the Market Narrative Engine for the simulation game "Adulting".
            Your goal is to teach the player how real-world events affect stock markets.
            When explaining price moves, invent realistic global events:
            - Public Company Announcements (Earnings misses/beats, CEO scandals, M&A)
            - Legislative/Regulatory (New bills passed, deregulation, tax hikes, subsidies)
            - Geopolitical/Macro (Wars, trade embargoes, global pandemics, inflation data)
            - Black Swan Events (Industrial accidents, cyber attacks, terror attacks)
            
            Your 'analyst_tip' MUST be educational. Break down the cause-and-effect of the news and provide actionable trading advice (e.g., "Tech stocks drop on chip shortages. Consider buying the dip or holding cash until volatility settles.").
            
            Return JSON only:
            {
              "headlines": [
                {
                  "title": "Headline string",
                  "body": "Brief explanation connecting the price move to a specific macro/global event.",
                  "sentiment": "bullish|bearish|neutral",
                  "asset_name": "Related Asset Name"
                }
              ],
              "market_mood": "cautiously_optimistic|volatile|bullish|etc",
              "market_mood_emoji": "📈",
              "analyst_tip": {
                "message": "Educational breakdown of the market forces at play, followed by concrete strategy advice.",
                "mentor": "Coach Chen"
              }
            }"""

            response_text = _call_gemini_api(prompt, system_instruction=system_prompt)
            if not response_text:
                return AIService._get_market_news_fallback(asset_changes)
            
            parsed = AIService._parse_json_response(response_text)
            return parsed or AIService._get_market_news_fallback(asset_changes)

        except Exception as e:
            logger.error(f"Error in generate_market_news: {e}")
            return AIService._get_market_news_fallback(asset_changes)

    @staticmethod
    def _get_market_news_fallback(asset_changes: Dict) -> Dict:
        """Fallback for market news when AI is down."""
        headlines = []
        for name, c in list(asset_changes.items())[:3]:
            sentiment = "bullish" if c['change_pct'] > 0 else "bearish"
            headlines.append({
                "title": f"{name} seeing {'gains' if c['change_pct'] > 0 else 'volatility'}",
                "body": f"Prices moved by {c['change_pct']:+.1f}% in today's trading session.",
                "sentiment": sentiment,
                "asset_name": name
            })
            
        return {
            "headlines": headlines,
            "market_mood": "volatile",
            "market_mood_emoji": "🌀",
            "analyst_tip": {
                "message": "Keep an eye on your stop losses. Volatility is the only constant.",
                "mentor": "Coach Chen"
            }
        }

    @staticmethod
    def _parse_json_response(text: str) -> Optional[Dict]:
        """Utility to strip markdown fences and parse JSON from Gemini."""
        if not text:
            return None
            
        raw_text = text.strip()
        
        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw_text = "\n".join(lines).strip()
            
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini: {e}. Raw: {raw_text[:100]}")
            return None

    @staticmethod
    def _get_void_fallback(content: str) -> Dict:
        """Fallback response for The Void when Gemini is down."""
        return {
            "mood": "anxious",
            "mood_emoji": "🌀",
            "message": "The void echoes your frustration. Silence is sometimes the loudest scream.",
            "empathy_line": "The void feels your weight.",
            "challenge": {
                "title": "Void Meditation",
                "description": "Check your dashboard and breathe. This too shall pass.",
                "reward_sanity": 2,
                "reward_xp": 10,
                "cta_screen": "/(tabs)/dashboard"
            }
        }

    # ── Contextual Greeting ────────────────────────────────────────────────

    @staticmethod
    def generate_greeting(
        mentor_role: str,
        mentor_name: str,
        username: str,
        metrics: Dict,
    ) -> Optional[Dict]:
        """
        Generate a contextual opening message when a player opens a mentor chat.
        Cached for 6 hours to avoid redundant calls.
        """
        from app.utils.ai_cache import get_cached_response, set_cached_response, make_cache_key
        from app import supabase

        # Check cache (greeting doesn't change frequently)
        cache_key = make_cache_key("greeting", mentor_role, username,
                                   str(int(metrics.get('net_worth', 0))))
        cached = get_cached_response(cache_key, supabase_client=supabase)
        if cached:
            return cached

        system_prompt = MENTOR_SYSTEM_PROMPTS.get(mentor_role, MENTOR_SYSTEM_PROMPTS['strategic'])
        financial_context = AIService._build_financial_context(username, metrics)

        prompt = (
            f"{system_prompt}\n\n"
            f"--- PLAYER FINANCIAL SNAPSHOT ---\n{financial_context}\n\n"
            f"The player just opened your chat. Generate a warm, contextual greeting "
            f"that acknowledges their current financial state. This is NOT a reply to a "
            f"message — it's the opening message they see when they enter the chat.\n\n"
            f"--- YOUR RESPONSE (valid JSON only, no markdown fences) ---"
        )

        try:
            response_text = _call_gemini_api(prompt)
            if not response_text:
                return AIService._fallback_greeting(mentor_role, username, metrics)

            parsed = AIService._parse_json_response(response_text)
            if not parsed:
                return AIService._fallback_greeting(mentor_role, username, metrics)
            result = {
                'message': parsed.get('message', f"Hey {username}!"),
                'tone': parsed.get('tone', 'encouraging'),
                'suggested_actions': parsed.get('suggested_actions', []),
                'follow_up_question': parsed.get('follow_up_question'),
                'relationship_points': 0,  # Greetings don't award points
            }

            # Cache for 6 hours
            set_cached_response(cache_key, result, ttl_seconds=21600, supabase_client=supabase)
            return result

        except Exception as e:
            logger.error(f"Greeting generation failed: {e}")
            return AIService._fallback_greeting(mentor_role, username, metrics)

    # ── Rate Limiting ──────────────────────────────────────────────────────

    @staticmethod
    def check_rate_limit(player_id: str, mentor_id: str) -> Dict:
        """
        Check if the player has remaining AI messages for this mentor today.
        Returns: { allowed: bool, remaining: int, resets_at: str }
        """
        from app.models.player_mentor_interaction import PlayerMentorInteraction
        from app import db

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        count = PlayerMentorInteraction.query.filter(
            PlayerMentorInteraction.player_id == uuid.UUID(player_id),
            PlayerMentorInteraction.mentor_id == uuid.UUID(mentor_id),
            PlayerMentorInteraction.is_player_message == True,
            PlayerMentorInteraction.sent_at >= today_start
        ).count()

        remaining = max(0, AIService.DAILY_MESSAGE_LIMIT - count)
        resets_at = (today_start + timedelta(days=1)).isoformat()

        return {
            'allowed': remaining > 0,
            'remaining': remaining,
            'resets_at': resets_at,
            'limit': AIService.DAILY_MESSAGE_LIMIT,
        }

    # ── Conversation History ───────────────────────────────────────────────

    @staticmethod
    def get_conversation_history(player_id: str, mentor_id: str) -> List[Dict]:
        """Fetch the last N interactions for this player-mentor pair."""
        from app.models.player_mentor_interaction import PlayerMentorInteraction

        interactions = PlayerMentorInteraction.query.filter_by(
            player_id=uuid.UUID(player_id),
            mentor_id=uuid.UUID(mentor_id),
        ).order_by(
            PlayerMentorInteraction.sent_at.asc()
        ).limit(AIService.CONVERSATION_HISTORY_DEPTH * 2).all()

        return [
            {
                'id': str(i.id),
                'message_content': i.message_content,
                'is_player_message': getattr(i, 'is_player_message', False),
                'sent_at': i.sent_at.isoformat() if i.sent_at else None,
                'action_taken': i.action_taken,
                'points_earned': i.points_earned or 0,
                'ai_metadata': getattr(i, 'ai_metadata', {}),
            }
            for i in interactions
        ]

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _build_financial_context(username: str, metrics: Dict) -> str:
        """Format player metrics into a readable context block for the AI."""
        return (
            f"Username: {username}\n"
            f"Net Worth: ${metrics.get('net_worth', 0):,.0f}\n"
            f"Cash: ${metrics.get('cash', 0):,.0f}\n"
            f"Total Assets: ${metrics.get('total_assets', 0):,.0f}\n"
            f"Total Liabilities: ${metrics.get('total_liabilities', 0):,.0f}\n"
            f"Monthly Income: ${metrics.get('monthly_income', 0):,.0f}\n"
            f"Monthly Debt Payments: ${metrics.get('monthly_debt_payments', 0):,.0f}\n"
            f"Debt-to-Income Ratio: {metrics.get('debt_to_income_ratio', 0):.0%}\n"
            f"Cash Ratio: {metrics.get('cash_ratio', 0):.0%}\n"
            f"Asset Concentration: {metrics.get('asset_concentration', 0):.0%}\n"
            f"Asset Types: {json.dumps(metrics.get('asset_types', {}))}\n"
            f"Credit Score: {metrics.get('credit_score', 650)}\n"
            f"Savings Rate: {metrics.get('savings_rate', 0):.0%}\n"
            f"Asset Count: {metrics.get('asset_count', 0)}\n"
            f"Income Sources: {metrics.get('income_sources_count', 1)}\n"
            f"Days Inactive: {metrics.get('days_inactive', 0)}\n"
            f"Account Age (months): {metrics.get('account_age_months', 0):.0f}\n"
            f"Sanity: {metrics.get('sanity', 100)}"
        )

    @staticmethod
    def _fallback_response(mentor_role: str, username: str, metrics: Dict) -> Dict:
        """Template-based fallback when AI is unavailable."""
        net_worth = metrics.get('net_worth', 0)
        dti = metrics.get('debt_to_income_ratio', 0)
        s_verdict = "not bad, but we can do better." if net_worth > 0 else "we need to change this. Now."
        r_verdict = "manageable." if dti < 0.4 else "concerning."
        e_verdict = "I see you are doing well — so proud!" if net_worth > 0 else "I know things are tough, but I believe in you."

        fallbacks = {
            'strategic': {
                'message': (
                    f"Hey {username}, I am reviewing your portfolio right now. "
                    f"Your net worth is ${net_worth:,.0f} — {s_verdict}\n\n"
                    f"Check your investments and let us build some momentum."
                ),
                'tone': 'tough_love',
            },
            'risk_analyst': {
                'message': (
                    f"Hi {username}, I have been looking at your numbers. "
                    f"Your debt-to-income is {dti:.0%} — {r_verdict}\n\n"
                    f"Let us review your financial position together."
                ),
                'tone': 'neutral',
            },
            'emotional': {
                'message': (
                    f"Sweetheart, I just wanted to check in on you. "
                    f"{e_verdict}\n\n"
                    f"Remember, I am always here for you.\n\nLove, Mom/Dad"
                ),
                'tone': 'encouraging',
            },
        }

        fallback = fallbacks.get(mentor_role, fallbacks['strategic'])
        return {
            'message': fallback['message'],
            'tone': fallback['tone'],
            'suggested_actions': [{
                'label': 'View Dashboard',
                'screen': '/(tabs)/index',
                'params': {},
                'icon': 'home',
            }],
            'follow_up_question': None,
            'relationship_points': 5,
        }

    @staticmethod
    def _fallback_greeting(mentor_role: str, username: str, metrics: Dict) -> Dict:
        """Template greeting when AI is unavailable."""
        greetings = {
            'strategic': f"Hey {username}, ready to level up your finances? Let's look at your portfolio.",
            'risk_analyst': f"Hi {username}, let's review your financial health today.",
            'emotional': f"Sweetheart, I'm so glad you're here. Let's talk.\n\nLove, Mom/Dad",
        }
        return {
            'message': greetings.get(mentor_role, f"Hey {username}!"),
            'tone': 'encouraging',
            'suggested_actions': [],
            'follow_up_question': None,
            'relationship_points': 0,
        }
