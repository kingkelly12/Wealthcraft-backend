-- Create assets table for user assets
CREATE TABLE public.assets (
  id TEXT PRIMARY KEY,                        
  name TEXT NOT NULL,                         
  category TEXT NOT NULL,                     
  price NUMERIC(12,2) NOT NULL DEFAULT 0,     
  price_change NUMERIC(12,2) DEFAULT 0,       
  price_change_percent NUMERIC(5,2) DEFAULT 0,
  monthly_income NUMERIC(12,2) DEFAULT 0,     
  description TEXT,                           
  risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high')) DEFAULT 'medium',
  roi NUMERIC(5,2) DEFAULT 0, 
  time_to_return TEXT DEFAULT 'unknown',                
  availability INTEGER DEFAULT 0,             
  total_supply INTEGER DEFAULT 0,             
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create liabilities table for debts, loans, etc.
CREATE TABLE public.liabilities (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  name TEXT NOT NULL,
  liability_type TEXT NOT NULL, -- 'credit_card', 'student_loan', 'mortgage', 'car_loan', etc.
  amount NUMERIC NOT NULL,
  interest_rate NUMERIC NOT NULL DEFAULT 0,
  monthly_payment NUMERIC NOT NULL DEFAULT 0,
  due_date TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Add a column to track P2P loan relationships in liabilities table
ALTER TABLE liabilities ADD COLUMN IF NOT EXISTS p2p_loan_id UUID REFERENCES p2p_loans(id);

-- Update the RLS policies to ensure proper data access
CREATE POLICY "Users can view their liabilities" ON liabilities
FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their liabilities" ON liabilities
FOR INSERT WITH CHECK (user_id = auth.uid());

-- Create a liability_items table for predefined liability options 
CREATE TABLE public.liability_items (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL, -- 'car', 'motorbike', 'boat', 'yacht', 'helicopter', 'aircraft', 'private_jet', etc.
  base_price NUMERIC NOT NULL,
  monthly_cost NUMERIC NOT NULL,
  description TEXT,
  image_url TEXT
);

-- Create a player_liabilities table to track user liabilities from predefined items
CREATE TABLE public.player_liabilities (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  player_id UUID NOT NULL,
  liability_id UUID NOT NULL,
  purchase_price NOT NULL, 
  monthly_cost NOT NULL,
  purchase_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  is_active BOOLEAN NOT NULL DEFAULT true
);

-- Create jobs table for career progression
CREATE TABLE public.jobs (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  title TEXT NOT NULL,
  company TEXT,
  salary NUMERIC NOT NULL DEFAULT 0,
  level TEXT NOT NULL DEFAULT 'entry',
  experience_months INTEGER NOT NULL DEFAULT 0,
  promotion_progress INTEGER NOT NULL DEFAULT 0, -- percentage to next promotion
  is_current BOOLEAN NOT NULL DEFAULT true,
  start_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  end_date TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create job_market table for available jobs 
CREATE TABLE public.job_market (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  industry TEXT NOT NULL,
  company TEXT NOT NULL,
  salary NUMERIC NOT NULL,
  level TEXT NOT NULL,
  experience_months INTEGER NOT NULL
);

-- Create rental_properties table for rental marketplace
CREATE TABLE public.rental_properties (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  property_type TEXT NOT NULL,
  monthly_rent INTEGER NOT NULL,
  location TEXT NOT NULL,
  amenities TEXT[] DEFAULT '{}'
);
  
-- Create courses table
CREATE TABLE public.courses (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL, -- 'finance', 'career', 'investing', etc.
  difficulty TEXT NOT NULL DEFAULT 'beginner', -- 'beginner', 'intermediate', 'advanced'
  duration_hours INTEGER NOT NULL DEFAULT 1,
  cost NUMERIC NOT NULL DEFAULT 0,
  salary_boost NUMERIC NOT NULL DEFAULT 0, -- potential salary increase
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create user_courses table for tracking course progress
CREATE TABLE public.user_courses (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  course_id UUID NOT NULL,
  progress INTEGER NOT NULL DEFAULT 0, -- percentage completed
  completed_at TIMESTAMP WITH TIME ZONE,
  started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id, course_id)
);

-- Create life_events table
CREATE TABLE public.life_events (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('opportunity', 'challenge', 'neutral', 'emergency', 'economic', 'career', 'personal', 'social', 'environmental', 'psychological')),
  impact_cash NUMERIC DEFAULT 0,
  impact_income NUMERIC DEFAULT 0,
  impact_expenses NUMERIC DEFAULT 0,
  impact_assets TEXT,
  time_limit_seconds INTEGER DEFAULT 604800, -- 7 days default
  icon_name TEXT DEFAULT 'Zap',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create life_event_choices table for event options
CREATE TABLE public.life_event_choices (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  life_event_id UUID NOT NULL REFERENCES public.life_events(id) ON DELETE CASCADE,
  choice_label TEXT NOT NULL,
  outcome_description TEXT NOT NULL,
  cost NUMERIC DEFAULT 0,
  benefit NUMERIC DEFAULT 0,
  choice_order INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create user_life_events table to track user interactions
CREATE TABLE public.user_life_events (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES public.profiles(user_id) ON DELETE CASCADE,
  life_event_id UUID NOT NULL REFERENCES public.life_events(id),
  choice_id UUID REFERENCES public.life_event_choices(id),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Table for mission-course relationships
CREATE TABLE public.mission_courses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  mission_id UUID NOT NULL REFERENCES integrated_missions(id) ON DELETE CASCADE,
  course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
  is_required BOOLEAN DEFAULT false,
  recommendation_level TEXT CHECK (recommendation_level IN ('recommended', 'optional', 'avoid')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(mission_id, course_id)
);

-- Table for mission-asset relationships
CREATE TABLE public.mission_assets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  mission_id UUID NOT NULL REFERENCES integrated_missions(id) ON DELETE CASCADE,
  asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  recommendation_level TEXT CHECK (recommendation_level IN ('required', 'recommended', 'optional', 'avoid')),
  allocation_percentage DECIMAL(5,2) DEFAULT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(mission_id, asset_id)
);

-- For courses table
ALTER TABLE courses ADD COLUMN IF NOT EXISTS mission_prerequisites text[] DEFAULT '{}';
ALTER TABLE courses ADD COLUMN IF NOT EXISTS unlocks_assets text[] DEFAULT '{}';
ALTER TABLE courses ADD COLUMN IF NOT EXISTS mission_only boolean DEFAULT false;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS difficulty_rating integer DEFAULT 1;
ALTER TABLE courses ADD COLUMN IF NOT EXISTS learning_path text;

-- For assets table
ALTER TABLE assets ADD COLUMN IF NOT EXISTS mission_prerequisites text[] DEFAULT '{}';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS recommended_for_mission text[] DEFAULT '{}';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS risk_education text;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS educational_tier text DEFAULT 'beginner';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS mission_only boolean DEFAULT false;
ALTER TABLE assets ADD COLUMN IF NOT EXISTS unlocks_on_purchase text[] DEFAULT '{}';

-- Enable RLS
ALTER TABLE public.life_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.life_event_choices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_life_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Anyone can view life events" ON public.life_events FOR SELECT USING (true);
CREATE POLICY "Anyone can view life event choices" ON public.life_event_choices FOR SELECT USING (true);
CREATE POLICY "Users can view their own life event history" ON public.user_life_events FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own life event history" ON public.user_life_events FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX idx_life_events_active ON public.life_events(is_active);
CREATE INDEX idx_life_event_choices_event_id ON public.life_event_choices(life_event_id);
CREATE INDEX idx_user_life_events_user_id ON public.user_life_events(user_id);
CREATE INDEX idx_user_life_events_created_at ON public.user_life_events(created_at DESC);

-- Add trigger for updated_at
CREATE TRIGGER update_life_events_updated_at 
  BEFORE UPDATE ON public.life_events 
  FOR EACH ROW 
  EXECUTE FUNCTION public.update_updated_at_column();

-- Enable RLS on all tables
ALTER TABLE public.liabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.family_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.life_goals ENABLE ROW LEVEL SECURITY;

-- RLS policies for liabilities
CREATE POLICY "Users can view their own liabilities" ON public.liabilities FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own liabilities" ON public.liabilities FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own liabilities" ON public.liabilities FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own liabilities" ON public.liabilities FOR DELETE USING (auth.uid() = user_id);

-- RLS policies for jobs
CREATE POLICY "Users can view their own jobs" ON public.jobs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own jobs" ON public.jobs FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own jobs" ON public.jobs FOR UPDATE USING (auth.uid() = user_id);

-- RLS policies for courses (public read, admin write)
CREATE POLICY "Anyone can view courses" ON public.courses FOR SELECT USING (true);

-- RLS policies for user_courses
CREATE POLICY "Users can view their own course progress" ON public.user_courses FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create their own course progress" ON public.user_courses FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own course progress" ON public.user_courses FOR UPDATE USING (auth.uid() = user_id);

-- Add triggers for updated_at
CREATE TRIGGER update_liabilities_updated_at BEFORE UPDATE ON public.liabilities FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON public.jobs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_family_members_updated_at BEFORE UPDATE ON public.family_members FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_life_goals_updated_at BEFORE UPDATE ON public.life_goals FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Create function to calculate net worth
CREATE OR REPLACE FUNCTION public.calculate_net_worth(user_id_param UUID)
RETURNS NUMERIC
LANGUAGE sql
STABLE
AS $$
  SELECT COALESCE(
    (SELECT SUM(value) FROM public.user_assets WHERE user_id = user_id_param) -
    (SELECT SUM(amount) FROM public.liabilities WHERE user_id = user_id_param),
    0
  );
$$;

-- Create function to calculate monthly income
CREATE OR REPLACE FUNCTION public.calculate_monthly_income(user_id_param UUID)
RETURNS NUMERIC
LANGUAGE sql
STABLE
AS $$
  SELECT COALESCE(
    (SELECT salary / 12 FROM public.jobs WHERE user_id = user_id_param AND is_current = true LIMIT 1) +
    (SELECT SUM(income) FROM public.family_members WHERE user_id = user_id_param),
    0
  );
$$;

-- Create a function to get random life events
CREATE OR REPLACE FUNCTION get_random_life_events(limit_count integer DEFAULT 1)
RETURNS SETOF life_events
LANGUAGE sql
STABLE
AS $$
  SELECT * 
  FROM life_events 
  WHERE is_active = true 
  ORDER BY random()
  LIMIT limit_count;
$$;

-- Function to get random active life event
CREATE OR REPLACE FUNCTION get_random_life_event()
RETURNS SETOF life_events
LANGUAGE sql
STABLE
AS $$
  SELECT * FROM life_events 
  WHERE is_active = true 
  ORDER BY random() 
  LIMIT 1;
$$;

-- Function to process life event choice
CREATE OR REPLACE FUNCTION process_life_event_choice(
  user_id_param UUID,
  life_event_id_param UUID,
  choice_id_param UUID
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
  choice_record life_event_choices%ROWTYPE;
  net_impact NUMERIC;
BEGIN
  -- Get choice details
  SELECT * INTO choice_record 
  FROM life_event_choices 
  WHERE id = choice_id_param;
  
  -- Calculate net impact
  net_impact := choice_record.benefit - choice_record.cost;
  
  -- Update user balance
  IF net_impact != 0 THEN
    UPDATE user_balances 
    SET current_balance = current_balance + net_impact
    WHERE user_id = user_id_param;
  END IF;
  
  -- Record the event
  INSERT INTO user_life_events (user_id, life_event_id, choice_id)
  VALUES (user_id_param, life_event_id_param, choice_id_param);
END;
$$;


-- Add column to track auto-selected choices
ALTER TABLE public.user_life_events 
ADD COLUMN was_auto_selected BOOLEAN DEFAULT FALSE;

-- Create index for better querying of auto-selected events
CREATE INDEX idx_user_life_events_auto_selected 
ON public.user_life_events(was_auto_selected);

-- Update the process_life_event_choice function to handle auto-selection
CREATE OR REPLACE FUNCTION process_life_event_choice(
  user_id_param UUID,
  life_event_id_param UUID,
  choice_id_param UUID,
  was_auto_selected_param BOOLEAN DEFAULT FALSE
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
  choice_record life_event_choices%ROWTYPE;
  net_impact NUMERIC;
BEGIN
  -- Get choice details
  SELECT * INTO choice_record 
  FROM life_event_choices 
  WHERE id = choice_id_param;
  
  -- Calculate net impact
  net_impact := choice_record.benefit - choice_record.cost;
  
  -- Update user balance
  IF net_impact != 0 THEN
    UPDATE user_balances 
    SET current_balance = current_balance + net_impact
    WHERE user_id = user_id_param;
  END IF;
  
  -- Record the event with auto-selection flag
  INSERT INTO user_life_events (user_id, life_event_id, choice_id, was_auto_selected)
  VALUES (user_id_param, life_event_id_param, choice_id_param, was_auto_selected_param);
END;
$$;

-- Create RLS policies for player_liabilities
CREATE POLICY "Users can view their own liabilities" 
ON public.player_liabilities 
FOR SELECT 
USING (auth.uid() = player_id);

CREATE POLICY "Users can create their own liabilities" 
ON public.player_liabilities 
FOR INSERT 
WITH CHECK (auth.uid() = player_id);

CREATE POLICY "Users can update their own liabilities" 
ON public.player_liabilities 
FOR UPDATE 
USING (auth.uid() = player_id);

CREATE POLICY "Users can delete their own liabilities" 
ON public.player_liabilities 
FOR DELETE 
USING (auth.uid() = player_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_player_liabilities_player_id ON public.player_liabilities(player_id);
CREATE INDEX IF NOT EXISTS idx_player_liabilities_active ON public.player_liabilities(is_active);