-- Add columns to user_life_events to track active events
ALTER TABLE public.user_life_events
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS viewed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS time_limit_seconds INTEGER DEFAULT 604800,
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE;

-- Create index for active events
CREATE INDEX IF NOT EXISTS idx_user_life_events_active_unresolved 
ON public.user_life_events(user_id, is_active) 
WHERE is_active = true AND resolved_at IS NULL;

-- Create index for expired events
CREATE INDEX IF NOT EXISTS idx_user_life_events_expires_at 
ON public.user_life_events(expires_at) 
WHERE is_active = true AND resolved_at IS NULL;

-- Create function to get active unresolved events for a user
CREATE OR REPLACE FUNCTION get_active_user_events(user_id_param UUID)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  life_event_id UUID,
  choice_id UUID,
  is_active BOOLEAN,
  viewed_at TIMESTAMP WITH TIME ZONE,
  time_limit_seconds INTEGER,
  expires_at TIMESTAMP WITH TIME ZONE,
  resolved_at TIMESTAMP WITH TIME ZONE,
  was_auto_selected BOOLEAN,
  created_at TIMESTAMP WITH TIME ZONE,
  event_title TEXT,
  event_description TEXT,
  event_type TEXT,
  impact_cash NUMERIC,
  impact_income NUMERIC,
  impact_expenses NUMERIC,
  impact_assets TEXT,
  icon_name TEXT
)
LANGUAGE sql
STABLE
AS $$
  SELECT 
    ule.id,
    ule.user_id,
    ule.life_event_id,
    ule.choice_id,
    ule.is_active,
    ule.viewed_at,
    ule.time_limit_seconds,
    ule.expires_at,
    ule.resolved_at,
    ule.was_auto_selected,
    ule.created_at,
    le.title,
    le.description,
    le.event_type,
    le.impact_cash,
    le.impact_income,
    le.impact_expenses,
    le.impact_assets,
    le.icon_name
  FROM public.user_life_events ule
  JOIN public.life_events le ON ule.life_event_id = le.id
  WHERE ule.user_id = user_id_param 
    AND ule.is_active = true 
    AND ule.resolved_at IS NULL
    AND (ule.expires_at IS NULL OR ule.expires_at > now())
  ORDER BY ule.viewed_at DESC
  LIMIT 1;
$$;

-- Create function to mark event as resolved
CREATE OR REPLACE FUNCTION resolve_user_event(
  event_id_param UUID,
  choice_id_param UUID
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE public.user_life_events
  SET 
    is_active = FALSE,
    choice_id = choice_id_param,
    resolved_at = now()
  WHERE id = event_id_param;
END;
$$;

-- Create function to create active event
CREATE OR REPLACE FUNCTION create_active_event(
  user_id_param UUID,
  life_event_id_param UUID,
  time_limit_seconds_param INTEGER DEFAULT 604800
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  new_event_id UUID;
BEGIN
  INSERT INTO public.user_life_events (
    user_id,
    life_event_id,
    is_active,
    viewed_at,
    time_limit_seconds,
    expires_at
  )
  VALUES (
    user_id_param,
    life_event_id_param,
    TRUE,
    now(),
    time_limit_seconds_param,
    now() + (time_limit_seconds_param || ' seconds')::INTERVAL
  )
  RETURNING id INTO new_event_id;
  
  RETURN new_event_id;
END;
$$;

-- Update RLS policy to allow users to update their own events
CREATE POLICY "Users can update their own life events" 
ON public.user_life_events 
FOR UPDATE 
USING (auth.uid() = user_id);

