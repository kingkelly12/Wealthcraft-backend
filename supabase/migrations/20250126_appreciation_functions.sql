-- Database functions required for monthly-appreciation Edge Function

-- Function 1: Get users who need appreciation processing
CREATE OR REPLACE FUNCTION get_users_for_appreciation()
RETURNS TABLE (user_id UUID) 
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT ua.user_id
  FROM user_assets ua
  INNER JOIN assets a ON ua.asset_id = a.id
  WHERE a.roi > 0 -- Only assets with positive ROI
    AND ua.quantity > 0; -- Only active holdings
END;
$$;

-- Function 2: Apply monthly asset appreciation
CREATE OR REPLACE FUNCTION apply_monthly_asset_appreciation(user_id_param UUID)
RETURNS TABLE (
  asset_id TEXT,
  asset_name TEXT,
  previous_value NUMERIC,
  new_value NUMERIC,
  appreciation_amount NUMERIC,
  appreciation_percent NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
  asset_record RECORD;
  monthly_roi NUMERIC;
  appreciation NUMERIC;
  new_val NUMERIC;
BEGIN
  FOR asset_record IN
    SELECT 
      ua.id as user_asset_id,
      ua.asset_id,
      a.name as asset_name,
      ua.value as current_value,
      ua.quantity,
      a.roi,
      a.category
    FROM user_assets ua
    INNER JOIN assets a ON ua.asset_id = a.id
    WHERE ua.user_id = user_id_param
      AND a.roi > 0
      AND ua.quantity > 0
      AND a.category NOT IN ('stocks', 'crypto') -- Exclude volatile assets
  LOOP
    -- Calculate monthly ROI (annual ROI / 12)
    monthly_roi := asset_record.roi / 12.0 / 100.0;
    
    -- Calculate appreciation
    appreciation := asset_record.current_value * monthly_roi;
    new_val := asset_record.current_value + appreciation;
    
    -- Update the user asset value
    UPDATE user_assets
    SET 
      value = new_val,
      updated_at = NOW()
    WHERE id = asset_record.user_asset_id;
    
    -- Return the appreciation details
    asset_id := asset_record.asset_id;
    asset_name := asset_record.asset_name;
    previous_value := asset_record.current_value;
    new_value := new_val;
    appreciation_amount := appreciation;
    appreciation_percent := monthly_roi * 100;
    
    RETURN NEXT;
  END LOOP;
  
  -- Update user's net worth
  UPDATE profiles
  SET 
    net_worth = (
      SELECT COALESCE(SUM(value), 0)
      FROM user_assets
      WHERE user_id = user_id_param
    ) - (
      SELECT COALESCE(SUM(amount), 0)
      FROM liabilities
      WHERE user_id = user_id_param
    ),
    updated_at = NOW()
  WHERE user_id = user_id_param;
  
  RETURN;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_users_for_appreciation() TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION apply_monthly_asset_appreciation(UUID) TO authenticated, anon, service_role;
