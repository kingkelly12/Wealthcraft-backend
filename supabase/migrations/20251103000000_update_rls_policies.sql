-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own assets" ON public.user_assets;
DROP POLICY IF EXISTS "Users can view their own balance" ON public.user_balances;
DROP POLICY IF EXISTS "Users can view loans they are involved in" ON public.loans;
DROP POLICY IF EXISTS "Users can view their own transactions" ON public.transactions;
DROP POLICY IF EXISTS "Users can view their own liabilities" ON public.player_liabilities;
DROP POLICY IF EXISTS "Users can view their own rentals" ON public.player_rentals;
DROP POLICY IF EXISTS "Anyone can view rental properties" ON public.rental_properties;

-- Enable RLS on rental_properties if not already enabled
ALTER TABLE public.rental_properties ENABLE ROW LEVEL SECURITY;

-- Drop any conflicting rental policies first
DROP POLICY IF EXISTS "Anyone can view rental properties" ON public.rental_properties;
DROP POLICY IF EXISTS "Users can view their own rentals" ON public.player_rentals;
DROP POLICY IF EXISTS "Users can create their own rentals" ON public.player_rentals;

-- Create new public viewing policies
CREATE POLICY "Anyone can view assets" 
ON public.user_assets 
FOR SELECT 
USING (true);

CREATE POLICY "Anyone can view balances" 
ON public.user_balances 
FOR SELECT 
USING (true);

CREATE POLICY "Anyone can view loans" 
ON public.loans 
FOR SELECT 
USING (true);

CREATE POLICY "Anyone can view transactions" 
ON public.transactions 
FOR SELECT 
USING (true);

CREATE POLICY "Anyone can view player liabilities" 
ON public.player_liabilities 
FOR SELECT 
USING (true);

-- Enable RLS for both tables
ALTER TABLE public.rental_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_rentals ENABLE ROW LEVEL SECURITY;

-- Drop any existing policies
DROP POLICY IF EXISTS "Anyone can view rental properties" ON public.rental_properties;
DROP POLICY IF EXISTS "Users can view their own rentals" ON public.player_rentals;
DROP POLICY IF EXISTS "Users can create their own rentals" ON public.player_rentals;
DROP POLICY IF EXISTS "Anyone can view player rentals" ON public.player_rentals;

-- Create new rental policies with better names and clear permissions
CREATE POLICY "Enable read access for all rental properties"
ON public.rental_properties
FOR SELECT
USING (true);

CREATE POLICY "Enable read access for all player rentals"
ON public.player_rentals
FOR SELECT
USING (true);

-- Allow authenticated users to modify their own rentals
CREATE POLICY "Enable authenticated user rental modifications"
ON public.player_rentals
FOR ALL
USING (auth.uid() = player_id)
WITH CHECK (auth.uid() = player_id);

-- Allow system-level changes to rental properties
CREATE POLICY "Enable system-level property modifications"
ON public.rental_properties
FOR ALL
USING (auth.uid() IS NOT NULL)
WITH CHECK (auth.uid() IS NOT NULL);

-- Keep existing modification policies
CREATE POLICY "Users can modify their own assets" 
ON public.user_assets 
FOR ALL 
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can modify their own balance" 
ON public.user_balances 
FOR ALL 
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can modify their own transactions" 
ON public.transactions 
FOR ALL 
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can modify their own player liabilities" 
ON public.player_liabilities 
FOR ALL 
USING (auth.uid() = player_id)
WITH CHECK (auth.uid() = player_id);

CREATE POLICY "Users can modify their own rentals" 
ON public.player_rentals 
FOR ALL 
USING (auth.uid() = player_id)
WITH CHECK (auth.uid() = player_id);