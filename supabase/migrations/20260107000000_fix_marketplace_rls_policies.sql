-- ============================================
-- FIX RLS POLICIES FOR MARKETPLACE TABLES
-- ============================================
-- This migration adds public read access to marketplace tables
-- (assets, liability_items) so that both web and mobile apps
-- can view available items for purchase.
--
-- IMPORTANT: These tables should be READ-ONLY for clients.
-- Only the backend (using service_role key) should modify them.
-- ============================================

-- ============================================
-- ASSETS TABLE (Marketplace - Stocks, Crypto, Real Estate, etc.)
-- ============================================

-- Enable RLS if not already enabled
ALTER TABLE public.assets ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Anyone can view marketplace assets" ON public.assets;
DROP POLICY IF EXISTS "Public read access to assets" ON public.assets;

-- Create public read policy for marketplace assets
CREATE POLICY "Public read access to assets"
ON public.assets
FOR SELECT
USING (true);

-- Note: No INSERT/UPDATE/DELETE policies for clients
-- Only service_role (backend) can modify marketplace assets

-- ============================================
-- LIABILITY_ITEMS TABLE (Marketplace - Cars, Boats, etc.)
-- ============================================

-- Enable RLS if not already enabled
ALTER TABLE public.liability_items ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Anyone can view liability items" ON public.liability_items;
DROP POLICY IF EXISTS "Public read access to liability items" ON public.liability_items;

-- Create public read policy for liability items
CREATE POLICY "Public read access to liability items"
ON public.liability_items
FOR SELECT
USING (true);

-- Note: No INSERT/UPDATE/DELETE policies for clients
-- Only service_role (backend) can modify marketplace items

-- ============================================
-- USER_ASSETS TABLE (Player-owned assets)
-- ============================================

-- Ensure RLS is enabled
ALTER TABLE public.user_assets ENABLE ROW LEVEL SECURITY;

-- Drop old restrictive policies
DROP POLICY IF EXISTS "Users can view their own assets" ON public.user_assets;

-- Create comprehensive policies for user_assets
CREATE POLICY "Users can view their own assets"
ON public.user_assets
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own assets"
ON public.user_assets
FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own assets"
ON public.user_assets
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own assets"
ON public.user_assets
FOR DELETE
USING (auth.uid() = user_id);

-- ============================================
-- PLAYER_LIABILITIES TABLE (Player-owned liabilities)
-- ============================================

-- Ensure RLS is enabled
ALTER TABLE public.player_liabilities ENABLE ROW LEVEL SECURITY;

-- Drop old policies
DROP POLICY IF EXISTS "Users can view their own liabilities" ON public.player_liabilities;

-- Create comprehensive policies for player_liabilities
CREATE POLICY "Users can view their own liabilities"
ON public.player_liabilities
FOR SELECT
USING (auth.uid() = player_id);

CREATE POLICY "Users can insert their own liabilities"
ON public.player_liabilities
FOR INSERT
WITH CHECK (auth.uid() = player_id);

CREATE POLICY "Users can update their own liabilities"
ON public.player_liabilities
FOR UPDATE
USING (auth.uid() = player_id)
WITH CHECK (auth.uid() = player_id);

CREATE POLICY "Users can delete their own liabilities"
ON public.player_liabilities
FOR DELETE
USING (auth.uid() = player_id);

-- ============================================
-- SUMMARY
-- ============================================
-- ✅ assets: Public read access (marketplace)
-- ✅ liability_items: Public read access (marketplace)
-- ✅ user_assets: Users can only access their own
-- ✅ player_liabilities: Users can only access their own
-- ============================================
