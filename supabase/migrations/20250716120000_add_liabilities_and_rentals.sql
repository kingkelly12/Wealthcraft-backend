-- Create rental_properties table
CREATE TABLE public.rental_properties (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  property_type TEXT NOT NULL,
  monthly_rent INTEGER NOT NULL,
  location TEXT NOT NULL,
  amenities TEXT[] DEFAULT '{}'
);

-- Create player_rentals junction table
CREATE TABLE IF NOT EXISTS public.player_rentals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  player_id UUID NOT NULL REFERENCES auth.users(id),
  property_id UUID NOT NULL REFERENCES public.rental_properties(id),
  monthly_rent INTEGER NOT NULL,
  is_active BOOLEAN DEFAULT true,
  rented_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  ended_at TIMESTAMP WITH TIME ZONE
);


-- Create monthly_deductions table for tracking automatic deductions
CREATE TABLE IF NOT EXISTS public.monthly_deductions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  player_id UUID NOT NULL REFERENCES auth.users(id),
  deduction_type VARCHAR(50) NOT NULL CHECK (deduction_type IN ('liability_cost', 'rent_payment')),
  amount DECIMAL(10,2) NOT NULL,
  reference_id UUID, -- Can reference player_liabilities.id or player_rentals.id
  deduction_date DATE NOT NULL,
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.rental_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.player_rentals ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Anyone can view rental properties" ON public.rental_properties FOR SELECT USING (true);
CREATE POLICY "Users can view their own rentals" ON public.player_rentals FOR SELECT USING (auth.uid() = player_id);
CREATE POLICY "Users can create their own rentals" ON public.player_rentals FOR INSERT WITH CHECK (auth.uid() = player_id);

-- Add rental_required flag to user profiles
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS rental_required BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS current_rental_id UUID REFERENCES public.player_rentals(id);

-- Add monthly_income to profiles for rent calculation
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS monthly_income DECIMAL(12,2) DEFAULT 0;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_player_liabilities_player_id ON public.player_liabilities(player_id);
CREATE INDEX IF NOT EXISTS idx_player_liabilities_active ON public.player_liabilities(is_active);
CREATE INDEX IF NOT EXISTS idx_player_rentals_player_id ON public.player_rentals(player_id);
CREATE INDEX IF NOT EXISTS idx_player_rentals_active ON public.player_rentals(is_active);
CREATE INDEX IF NOT EXISTS idx_rental_properties_available ON public.rental_properties(is_available);
CREATE INDEX IF NOT EXISTS idx_monthly_deductions_player_date ON public.monthly_deductions(player_id, deduction_date);

-- Ensure a player can only have one active rental
CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_rental_per_player ON public.player_rentals(player_id) WHERE is_active;





