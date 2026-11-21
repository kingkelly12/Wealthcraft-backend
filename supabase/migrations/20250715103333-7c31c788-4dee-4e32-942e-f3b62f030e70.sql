-- Create profiles table for user game data
CREATE TABLE public.profiles (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE NOT NULL,
  net_worth DECIMAL(15,2) DEFAULT 0,
  monthly_income DECIMAL(15,2) DEFAULT 0,
  credit_score INTEGER DEFAULT 650,
  wealth_level TEXT DEFAULT 'Beginner' CHECK (wealth_level IN ('Beginner', 'Millionaire', 'Decamillionaire', 'Centimillionaire', 'Billionaire', 'Decabillionaire', 'Centibillionaire')),
  experience_points INTEGER DEFAULT 0,
  push_token TEXT,
  push_token_updated_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  profile_picture_url TEXT DEFAULT 'https://example.com/default-profile.png',
);

-- Create chat_messages table for user communications
CREATE TABLE public.chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  recipient_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'read')),
  type TEXT NOT NULL DEFAULT 'text' CHECK (type IN ('text', 'file', 'image')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- New missions table
CREATE TABLE integrated_missions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  short_description TEXT,
  icon TEXT DEFAULT '🎯',
  category TEXT NOT NULL CHECK (category IN (
    'career_path', 'investment', 'debt_management', 'business_growth',
    'passive_income', 'wealth_preservation', 'crisis_response', 'lifestyle_balance'
  )),
  difficulty TEXT NOT NULL DEFAULT 'beginner' CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
  duration_months INTEGER NOT NULL DEFAULT 12,
  learning_objectives TEXT[] DEFAULT '{}',
  affects_main_game BOOLEAN NOT NULL DEFAULT TRUE,
  income_multiplier FLOAT NOT NULL DEFAULT 1.0,
  expense_multiplier FLOAT NOT NULL DEFAULT 1.0,
  can_change_job BOOLEAN NOT NULL DEFAULT TRUE,
  can_buy_assets BOOLEAN NOT NULL DEFAULT TRUE,
  can_take_loans BOOLEAN NOT NULL DEFAULT TRUE,
  can_rent_property BOOLEAN NOT NULL DEFAULT TRUE,
  can_sell_assets BOOLEAN NOT NULL DEFAULT TRUE,
  can_buy_lifestyle_items BOOLEAN NOT NULL DEFAULT TRUE,
  allowed_asset_types TEXT[] DEFAULT NULL,
  max_loan_amount NUMERIC DEFAULT NULL,
  allowed_loan_types TEXT[] DEFAULT NULL,
  max_monthly_spending NUMERIC DEFAULT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Decision points table
CREATE TABLE mission_decision_points (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id UUID REFERENCES integrated_missions(id) ON DELETE CASCADE,
  month INTEGER NOT NULL CHECK (month >= 1),
  is_required BOOLEAN DEFAULT TRUE,
  auto_resolve_after_days INTEGER DEFAULT NULL,
  auto_resolve_option_id UUID DEFAULT NULL, 
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  context TEXT,
  learning_lesson TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(mission_id, month)
);

-- Decision options table
CREATE TABLE mission_decision_options (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_point_id UUID REFERENCES mission_decision_points(id) ON DELETE CASCADE,
  label TEXT NOT NULL,
  description TEXT NOT NULL,
  game_action_type TEXT CHECK (game_action_type IN ('buy_asset', 'take_loan', 'change_job', 'sell_asset', 'custom', 'none')),
  game_action_data JSONB DEFAULT '{}',
  immediate_cash NUMERIC DEFAULT 0,
  monthly_income_change NUMERIC DEFAULT 0,
  monthly_expense_change NUMERIC DEFAULT 0,
  asset_impact NUMERIC DEFAULT 0,
  debt_impact NUMERIC DEFAULT 0,
  happiness_change INTEGER DEFAULT 0 CHECK (happiness_change BETWEEN -100 AND 100),
  stress_change INTEGER DEFAULT 0 CHECK (stress_change BETWEEN -100 AND 100),
  motivation_change INTEGER DEFAULT 0 CHECK (motivation_change BETWEEN -100 AND 100),
  risk_level TEXT DEFAULT 'medium' CHECK (risk_level IN ('low', 'medium', 'high')),
  success_probability FLOAT CHECK (success_probability BETWEEN 0 AND 1),
  unlocks_decision_id UUID REFERENCES mission_decision_points(id), 
  blocks_decision_id UUID REFERENCES mission_decision_points(id),  
  affects_story BOOLEAN DEFAULT FALSE,
  hidden BOOLEAN DEFAULT FALSE,
  condition TEXT,
  option_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Success criteria table (FIXED ERROR HERE)
CREATE TABLE mission_success_criteria (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
  mission_id UUID REFERENCES integrated_missions(id) ON DELETE CASCADE,
  metric TEXT NOT NULL CHECK (metric IN (
    'net_worth', 'monthly_income', 'debt_ratio', 'credit_score',
    'asset_value', 'passive_income', 'business_value', 'custom'
  )),
  target NUMERIC NOT NULL,
  comparison TEXT NOT NULL CHECK (comparison IN ('greater_than', 'less_than', 'equals', 'between')),
  target_min NUMERIC,
  custom_metric_formula TEXT,
  label TEXT NOT NULL,
  description TEXT,
  icon TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(mission_id, metric)
);

-- Mission events
CREATE TABLE integrated_mission_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id UUID REFERENCES integrated_missions(id) ON DELETE CASCADE,
  trigger_month INTEGER NOT NULL,
  trigger_type TEXT NOT NULL CHECK (trigger_type IN ('month', 'metric', 'probability')),
  trigger_condition TEXT,
  probability FLOAT DEFAULT 1.0 CHECK (probability BETWEEN 0 AND 1),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('market_event', 'personal_event', 'opportunity', 'crisis')),
  immediate_cash NUMERIC DEFAULT 0,
  monthly_income_change NUMERIC DEFAULT 0,
  asset_impact NUMERIC DEFAULT 0,
  has_choices BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Event choices
CREATE TABLE mission_event_choices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID REFERENCES integrated_mission_events(id) ON DELETE CASCADE,
  label TEXT NOT NULL,
  description TEXT,
  financial_impact NUMERIC NOT NULL,
  risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high')),
  choice_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Player progress
CREATE TABLE player_mission_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  player_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
  mission_id UUID NOT NULL REFERENCES integrated_missions(id) ON DELETE CASCADE,
  is_active BOOLEAN DEFAULT FALSE,
  is_completed BOOLEAN DEFAULT FALSE,
  is_failed BOOLEAN DEFAULT FALSE,
  current_month INTEGER DEFAULT 1,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  failed_at TIMESTAMPTZ,
  abandoned_at TIMESTAMPTZ,
  constraints_applied JSONB NOT NULL DEFAULT '{}',
  game_state_snapshot JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(player_id, mission_id)
);

-- Player decisions
CREATE TABLE player_mission_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  player_mission_id UUID REFERENCES player_mission_progress(id) ON DELETE CASCADE,
  decision_point_id UUID NOT NULL REFERENCES mission_decision_points(id), -- Added Reference
  chosen_option_id UUID NOT NULL REFERENCES mission_decision_options(id),  -- Added Reference
  month_made INTEGER NOT NULL,
  decision_data JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(player_mission_id, decision_point_id)
);

-- Success tracking
CREATE TABLE player_mission_success_tracking (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  player_mission_id UUID REFERENCES player_mission_progress(id) ON DELETE CASCADE,
  criteria_id UUID NOT NULL REFERENCES mission_success_criteria(id), -- Added Reference
  current_value NUMERIC DEFAULT 0,
  is_met BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(player_mission_id, criteria_id)
);

-- Completion results
CREATE TABLE mission_completion_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id UUID NOT NULL REFERENCES integrated_missions(id) ON DELETE CASCADE, -- Added Reference
  player_mission_id UUID NOT NULL REFERENCES player_mission_progress(id) ON DELETE CASCADE, -- Added Reference
  player_id UUID NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
  completed BOOLEAN NOT NULL,
  failed BOOLEAN NOT NULL,
  abandoned BOOLEAN NOT NULL,
  duration_months INTEGER NOT NULL,
  net_worth_change NUMERIC NOT NULL,
  income_change NUMERIC NOT NULL,
  credit_score_change INTEGER NOT NULL,
  criteria_met INTEGER NOT NULL,
  criteria_total INTEGER NOT NULL,
  success_percentage FLOAT NOT NULL,
  rewards_earned JSONB NOT NULL DEFAULT '[]',
  total_cash_reward NUMERIC NOT NULL DEFAULT 0,
  learning_score INTEGER CHECK (learning_score BETWEEN 0 AND 100),
  financial_iq_gain INTEGER,
  completion_message TEXT,
  completed_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Story events table
CREATE TABLE mission_story_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id UUID REFERENCES integrated_missions(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  emoji TEXT DEFAULT '📖',
  narrative TEXT NOT NULL,
  financial_context TEXT,
  story_type TEXT NOT NULL CHECK (story_type IN (
    'emotional', 'milestone', 'decision_point', 'crisis', 
    'opportunity', 'reflection', 'opening'
  )),
  
  trigger_type TEXT NOT NULL CHECK (trigger_type IN (
    'mission_start', 'month', 'threshold', 'decision', 'custom'
  )),
  trigger_value INTEGER, -- For month-based triggers
  trigger_condition TEXT, -- For threshold triggers (e.g., 'first_profit_month')
  probability FLOAT DEFAULT 1.0 CHECK (probability BETWEEN 0 AND 1),
  audio_cue TEXT CHECK (audio_cue IN (
    'decision', 'success', 'crisis', 'neutral', 'milestone'
  )),
  background_image TEXT,
  mood_color TEXT,
  happiness_change INTEGER DEFAULT 0 CHECK (happiness_change BETWEEN -100 AND 100),
  stress_change INTEGER DEFAULT 0 CHECK (stress_change BETWEEN -100 AND 100),
  motivation_change INTEGER DEFAULT 0 CHECK (motivation_change BETWEEN -100 AND 100),
  immediate_cash NUMERIC DEFAULT 0,
  display_order INTEGER NOT NULL DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(mission_id, display_order)
);

-- Player story progress tracking
CREATE TABLE player_story_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  player_mission_id UUID REFERENCES player_mission_progress(id) ON DELETE CASCADE,
  story_event_id UUID REFERENCES mission_story_events(id) ON DELETE CASCADE,
  has_triggered BOOLEAN DEFAULT FALSE,
  has_been_viewed BOOLEAN DEFAULT FALSE,
  triggered_at TIMESTAMPTZ,
  viewed_at TIMESTAMPTZ,
  game_state_snapshot JSONB DEFAULT '{}',
  mission_month INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(player_mission_id, story_event_id)
);


-- Create user_follows table
CREATE TABLE user_follows (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  follower_id UUID REFERENCES profiles(user_id) ON DELETE CASCADE,
  following_id UUID REFERENCES profiles(user_id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(follower_id, following_id)
);

-- Enable Row Level Security for chat_messages
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for chat_messages
CREATE POLICY "Users can view messages they are involved in"
ON public.chat_messages
FOR SELECT
USING (auth.uid() = sender_id OR auth.uid() = recipient_id);

CREATE POLICY "Users can send messages"
ON public.chat_messages
FOR INSERT
WITH CHECK (auth.uid() = sender_id);

CREATE POLICY "Users can update message status for received messages"
ON public.chat_messages
FOR UPDATE
USING (auth.uid() = recipient_id)
WITH CHECK (auth.uid() = recipient_id);

-- Drop existing foreign key constraints
ALTER TABLE public.chat_messages DROP CONSTRAINT IF EXISTS chat_messages_sender_id_fkey;
ALTER TABLE public.chat_messages DROP CONSTRAINT IF EXISTS chat_messages_recipient_id_fkey;

-- Add correct foreign key constraints to profiles table
ALTER TABLE public.chat_messages ADD CONSTRAINT chat_messages_sender_id_fkey
  FOREIGN KEY (sender_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE;

ALTER TABLE public.chat_messages ADD CONSTRAINT chat_messages_recipient_id_fkey
  FOREIGN KEY (recipient_id) REFERENCES public.profiles(user_id) ON DELETE CASCADE;

CREATE INDEX idx_profiles_push_token ON profiles(push_token);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender_id ON public.chat_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_recipient_id ON public.chat_messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON public.chat_messages(timestamp DESC);


-- Create index for better performance
CREATE INDEX idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX idx_user_follows_following ON user_follows(following_id);

-- Create indexes for performance
CREATE INDEX idx_integrated_missions_category ON integrated_missions(category);
CREATE INDEX idx_integrated_missions_difficulty ON integrated_missions(difficulty);
CREATE INDEX idx_player_mission_progress_player_id ON player_mission_progress(player_id);
CREATE INDEX idx_player_mission_progress_is_active ON player_mission_progress(is_active);
CREATE INDEX idx_mission_decision_points_mission_id ON mission_decision_points(mission_id);
CREATE INDEX idx_mission_success_criteria_mission_id ON mission_success_criteria(mission_id);

CREATE INDEX idx_mission_story_events_mission_id ON mission_story_events(mission_id);
CREATE INDEX idx_mission_story_events_trigger ON mission_story_events(trigger_type, trigger_value);
CREATE INDEX idx_player_story_progress_player_mission ON player_story_progress(player_mission_id);
CREATE INDEX idx_player_story_progress_triggered ON player_story_progress(has_triggered, has_been_viewed);

-- Enable RLS
ALTER TABLE user_follows ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view all follows" ON user_follows
  FOR SELECT USING (true);

CREATE POLICY "Users can insert their own follows" ON user_follows
  FOR INSERT WITH CHECK (auth.uid() = follower_id);

CREATE POLICY "Users can delete their own follows" ON user_follows
  FOR DELETE USING (auth.uid() = follower_id);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create policies for user access
CREATE POLICY "Users can view all profiles" 
ON public.profiles 
FOR SELECT 
USING (true);

CREATE POLICY "Users can create their own profile" 
ON public.profiles 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile" 
ON public.profiles 
FOR UPDATE 
USING (auth.uid() = user_id);

-- Allow users to upload their own profile pictures
CREATE POLICY "Users can upload their own profile pictures" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'avatars' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Allow users to update their own profile pictures
CREATE POLICY "Users can update their own profile pictures" ON storage.objects
FOR UPDATE USING (bucket_id = 'avatars' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Allow users to delete their own profile pictures
CREATE POLICY "Users can delete their own profile pictures" ON storage.objects
FOR DELETE USING (bucket_id = 'avatars' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Allow public access to view profile pictures
CREATE POLICY "Public can view profile pictures" ON storage.objects
FOR SELECT USING (bucket_id = 'avatars');

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Create function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
  INSERT INTO public.profiles (user_id, username)
  VALUES (
    NEW.id, 
    COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1))
  );
  RETURN NEW;
END;
$$;

-- Trigger to create profile when user signs up
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- Function to start a mission with proper state snapshot
CREATE OR REPLACE FUNCTION start_integrated_mission(
  p_player_id UUID,
  p_mission_id UUID
) RETURNS UUID AS $$
DECLARE
  v_player_mission_id UUID;
  v_mission_data integrated_missions%ROWTYPE;
  v_player_profile profiles%ROWTYPE;
BEGIN
  -- Get mission data
  SELECT * INTO v_mission_data FROM integrated_missions WHERE id = p_mission_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Mission not found: %', p_mission_id;
  END IF;
  
  -- Get player current state
  SELECT * INTO v_player_profile FROM profiles WHERE user_id = p_player_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Player not found: %', p_player_id;
  END IF;
  
  -- Check if player already has active mission
  IF EXISTS (SELECT 1 FROM player_mission_progress 
             WHERE player_id = p_player_id AND is_active = TRUE) THEN
    RAISE EXCEPTION 'Player already has an active mission';
  END IF;
  
  -- Create mission progress record
  INSERT INTO player_mission_progress (
    player_id, mission_id, is_active,
    constraints_applied, game_state_snapshot
  ) VALUES (
    p_player_id, p_mission_id, TRUE,
    jsonb_build_object(
      'income_multiplier', v_mission_data.income_multiplier,
      'expense_multiplier', v_mission_data.expense_multiplier,
      'can_change_job', v_mission_data.can_change_job,
      'can_buy_assets', v_mission_data.can_buy_assets,
      'can_take_loans', v_mission_data.can_take_loans,
      'can_rent_property', v_mission_data.can_rent_property,
      'can_sell_assets', v_mission_data.can_sell_assets,
      'can_buy_lifestyle_items', v_mission_data.can_buy_lifestyle_items,
      'allowed_asset_types', v_mission_data.allowed_asset_types,
      'max_loan_amount', v_mission_data.max_loan_amount,
      'allowed_loan_types', v_mission_data.allowed_loan_types,
      'max_monthly_spending', v_mission_data.max_monthly_spending
    ),
    jsonb_build_object(
      'net_worth', v_player_profile.net_worth,
      'monthly_income', v_player_profile.monthly_income,
      'credit_score', v_player_profile.credit_score,
      'started_at', NOW()
    )
  ) RETURNING id INTO v_player_mission_id;
  
  -- Initialize success criteria tracking
  INSERT INTO player_mission_success_tracking (player_mission_id, criteria_id, current_value, is_met)
  SELECT 
    v_player_mission_id,
    sc.id,
    CASE sc.metric
      WHEN 'net_worth' THEN v_player_profile.net_worth
      WHEN 'monthly_income' THEN v_player_profile.monthly_income
      WHEN 'credit_score' THEN v_player_profile.credit_score
      ELSE 0
    END,
    FALSE
  FROM mission_success_criteria sc
  WHERE sc.mission_id = p_mission_id;
  
  RETURN v_player_mission_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check mission progress monthly
CREATE OR REPLACE FUNCTION check_mission_progress(
  p_player_mission_id UUID
) RETURNS VOID AS $$
DECLARE
  v_mission_progress player_mission_progress%ROWTYPE;
  v_mission_data integrated_missions%ROWTYPE;
  v_player_profile profiles%ROWTYPE;
BEGIN
  -- Get mission progress
  SELECT * INTO v_mission_progress FROM player_mission_progress WHERE id = p_player_mission_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Mission progress not found: %', p_player_mission_id;
  END IF;
  
  -- Get mission data
  SELECT * INTO v_mission_data FROM integrated_missions WHERE id = v_mission_progress.mission_id;
  
  -- Get current player state
  SELECT * INTO v_player_profile FROM profiles WHERE user_id = v_mission_progress.player_id;
  
  -- Update success criteria tracking
  UPDATE player_mission_success_tracking pmst
  SET 
    current_value = CASE sc.metric
      WHEN 'net_worth' THEN v_player_profile.net_worth
      WHEN 'monthly_income' THEN v_player_profile.monthly_income
      WHEN 'credit_score' THEN v_player_profile.credit_score
      WHEN 'asset_value' THEN (
        SELECT COALESCE(SUM(value), 0) 
        FROM user_assets 
        WHERE user_id = v_mission_progress.player_id
      )
      WHEN 'debt_ratio' THEN (
        CASE WHEN v_player_profile.monthly_income > 0 THEN
          (SELECT COALESCE(SUM(monthly_payment), 0) 
           FROM liabilities 
           WHERE user_id = v_mission_progress.player_id) / v_player_profile.monthly_income
        ELSE 1 END
      )
      ELSE pmst.current_value
    END,
    is_met = CASE sc.metric
      WHEN 'net_worth' THEN v_player_profile.net_worth >= sc.target
      WHEN 'monthly_income' THEN v_player_profile.monthly_income >= sc.target
      WHEN 'credit_score' THEN v_player_profile.credit_score >= sc.target
      WHEN 'debt_ratio' THEN (
        CASE WHEN v_player_profile.monthly_income > 0 THEN
          (SELECT COALESCE(SUM(monthly_payment), 0) 
           FROM liabilities 
           WHERE user_id = v_mission_progress.player_id) / v_player_profile.monthly_income <= sc.target
        ELSE FALSE END
      )
      ELSE pmst.is_met
    END,
    updated_at = NOW()
  FROM mission_success_criteria sc
  WHERE pmst.criteria_id = sc.id 
    AND pmst.player_mission_id = p_player_mission_id;
  
  -- Check if mission is complete (all criteria met)
  IF NOT EXISTS (
    SELECT 1 FROM player_mission_success_tracking 
    WHERE player_mission_id = p_player_mission_id AND is_met = FALSE
  ) THEN
    -- Mission completed!
    UPDATE player_mission_progress
    SET 
      is_active = FALSE,
      is_completed = TRUE,
      completed_at = NOW(),
      updated_at = NOW()
    WHERE id = p_player_mission_id;
    
    -- Record completion results
    INSERT INTO mission_completion_results (
      mission_id, player_mission_id, player_id,
      completed, failed, abandoned,
      duration_months, net_worth_change, income_change, credit_score_change,
      criteria_met, criteria_total, success_percentage,
      rewards_earned, total_cash_reward,
      learning_score, financial_iq_gain,
      completion_message, completed_at
    ) VALUES (
      v_mission_progress.mission_id, p_player_mission_id, v_mission_progress.player_id,
      TRUE, FALSE, FALSE,
      v_mission_progress.current_month,
      v_player_profile.net_worth - (v_mission_progress.game_state_snapshot->>'net_worth')::NUMERIC,
      v_player_profile.monthly_income - (v_mission_progress.game_state_snapshot->>'monthly_income')::NUMERIC,
      v_player_profile.credit_score - (v_mission_progress.game_state_snapshot->>'credit_score')::INTEGER,
      (SELECT COUNT(*) FROM player_mission_success_tracking WHERE player_mission_id = p_player_mission_id AND is_met = TRUE),
      (SELECT COUNT(*) FROM player_mission_success_tracking WHERE player_mission_id = p_player_mission_id),
      100.0, -- All criteria met
      v_mission_data.rewards,
      0, -- Calculate based on rewards
      85, -- Placeholder learning score
      10, -- Placeholder IQ gain
      'Congratulations! You completed the mission successfully!',
      NOW()
    );
  END IF;
  
  -- Advance month if mission still active
  IF v_mission_progress.is_active THEN
    UPDATE player_mission_progress
    SET 
      current_month = current_month + 1,
      updated_at = NOW()
    WHERE id = p_player_mission_id;
    
    -- Check for decision points this month
    -- (You'll implement decision point triggering logic in application)
  END IF;
END;
$$ LANGUAGE plpgsql;