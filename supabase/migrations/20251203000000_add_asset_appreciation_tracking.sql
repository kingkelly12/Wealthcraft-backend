-- Add columns to user_assets table for tracking asset appreciation
ALTER TABLE public.user_assets
ADD COLUMN IF NOT EXISTS roi NUMERIC(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS monthly_appreciation NUMERIC(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS time_to_return TEXT,
ADD COLUMN IF NOT EXISTS last_appreciation_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS appreciation_count INTEGER DEFAULT 0;

-- Create index for querying assets that need appreciation calculation
CREATE INDEX IF NOT EXISTS idx_user_assets_appreciation 
ON public.user_assets(user_id, last_appreciation_date) 
WHERE asset_type != 'cash';

-- Create function to calculate and apply asset appreciation for a user
CREATE OR REPLACE FUNCTION apply_monthly_asset_appreciation(user_id_param UUID)
RETURNS TABLE (
  asset_id UUID,
  asset_name TEXT,
  previous_value NUMERIC,
  new_value NUMERIC,
  appreciation_amount NUMERIC,
  appreciation_percent NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_asset RECORD;
  v_monthly_roi NUMERIC;
  v_time_factor NUMERIC;
  v_new_value NUMERIC;
  v_appreciation_amount NUMERIC;
  v_appreciation_percent NUMERIC;
  v_current_date TIMESTAMP WITH TIME ZONE := now();
  v_current_month INTEGER := EXTRACT(MONTH FROM v_current_date);
  v_current_year INTEGER := EXTRACT(YEAR FROM v_current_date);
  v_last_month_date DATE;
BEGIN
  -- Get last day of previous month
  v_last_month_date := (DATE_TRUNC('month', v_current_date::DATE) - INTERVAL '1 day')::DATE;

  -- Loop through all non-cash assets for the user
  FOR v_asset IN 
    SELECT id, name, value, roi, time_to_return, asset_type, last_appreciation_date
    FROM public.user_assets
    WHERE user_id = user_id_param 
    AND asset_type != 'cash'
    AND roi > 0
  LOOP
    -- Check if we already processed this month
    IF v_asset.last_appreciation_date IS NOT NULL THEN
      IF EXTRACT(MONTH FROM v_asset.last_appreciation_date) = v_current_month 
         AND EXTRACT(YEAR FROM v_asset.last_appreciation_date) = v_current_year THEN
        CONTINUE; -- Skip if already appreciated this month
      END IF;
    END IF;

    -- Calculate monthly ROI
    v_monthly_roi := v_asset.roi / 100 / 12;

    -- Calculate time factor based on time_to_return (default 1.0 if not specified)
    v_time_factor := CASE 
      WHEN v_asset.time_to_return = 'short_term' THEN 1.5
      WHEN v_asset.time_to_return = 'medium_term' THEN 1.0
      WHEN v_asset.time_to_return = 'long_term' THEN 0.8
      ELSE 1.0
    END;

    -- Calculate new value with compound interest
    v_new_value := v_asset.value * (1 + v_monthly_roi * v_time_factor);
    v_appreciation_amount := v_new_value - v_asset.value;
    v_appreciation_percent := CASE 
      WHEN v_asset.value > 0 THEN (v_appreciation_amount / v_asset.value) * 100
      ELSE 0
    END;

    -- Update the asset with new value and appreciation tracking
    UPDATE public.user_assets
    SET 
      value = v_new_value,
      monthly_appreciation = v_appreciation_amount,
      last_appreciation_date = v_current_date,
      appreciation_count = appreciation_count + 1,
      updated_at = v_current_date
    WHERE id = v_asset.id;

    -- Return appreciation record for notifications
    RETURN QUERY SELECT 
      v_asset.id,
      v_asset.name,
      v_asset.value,
      v_new_value,
      v_appreciation_amount,
      v_appreciation_percent;
  END LOOP;
END;
$$;

-- Create function to get all users that need appreciation processing
CREATE OR REPLACE FUNCTION get_users_for_appreciation()
RETURNS TABLE (user_id UUID)
LANGUAGE sql
STABLE
AS $$
  SELECT DISTINCT ua.user_id
  FROM public.user_assets ua
  WHERE ua.asset_type != 'cash'
  AND ua.roi > 0
  AND (ua.last_appreciation_date IS NULL 
       OR DATE(ua.last_appreciation_date) < CURRENT_DATE);
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION apply_monthly_asset_appreciation(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_users_for_appreciation() TO authenticated, service_role;
