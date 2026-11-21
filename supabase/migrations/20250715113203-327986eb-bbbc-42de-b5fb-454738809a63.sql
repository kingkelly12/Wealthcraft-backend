-- Create loan table for P2P lending
CREATE TABLE public.p2p_loans (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  lender_id UUID NOT NULL REFERENCES public.profiles(user_id),
  borrower_id UUID REFERENCES public.profiles(user_id),
  amount NUMERIC NOT NULL,
  interest_rate NUMERIC NOT NULL,
  term_months INTEGER NOT NULL,
  purpose TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'completed', 'defaulted')),
  monthly_payment NUMERIC,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  funded_at TIMESTAMP WITH TIME ZONE,
  due_date TIMESTAMP WITH TIME ZONE
);

-- loan_repayments table
CREATE TABLE loan_repayments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  loan_id UUID REFERENCES p2p_loans(id),
  amount DECIMAL(10,2),
  due_date TIMESTAMP,
  payment_date TIMESTAMP,
  status VARCHAR(20), -- 'pending', 'paid', 'late', 'missed'
  created_at TIMESTAMP DEFAULT NOW()
);

-- Add columns to p2p_loans if not exists
ALTER TABLE p2p_loans ADD COLUMN IF NOT EXISTS collateral_amount DECIMAL(10,2);
ALTER TABLE p2p_loans ADD COLUMN IF NOT EXISTS next_payment_date TIMESTAMP;
ALTER TABLE p2p_loans ADD COLUMN IF NOT EXISTS remaining_balance DECIMAL(10,2);

-- Create bank_loans table for traditional bank loans
CREATE TABLE bank_loans (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  borrower_id UUID REFERENCES public.profiles(user_id),
  type TEXT NOT NULL,
  amount NUMERIC NOT NULL,
  interest_rate NUMERIC NOT NULL,
  term INTEGER NOT NULL,
  monthly_payment NUMERIC NOT NULL,
  total_interest NUMERIC NOT NULL,
  credit_required INTEGER NOT NULL,
  status TEXT NOT NULL,
  collateral TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  funded_at TIMESTAMP WITH TIME ZONE,
  due_date TIMESTAMP WITH TIME ZONE
);

-- Create user_balances table for real-time balance tracking
CREATE TABLE public.user_balances (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES public.profiles(user_id) UNIQUE,
  current_balance NUMERIC NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create transactions table for financial tracking
CREATE TABLE public.transactions (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES public.profiles(user_id),
  type TEXT NOT NULL CHECK (type IN ('income', 'expense', 'investment', 'loan_payment', 'loan_disbursement')),
  category TEXT NOT NULL,
  amount NUMERIC NOT NULL,
  description TEXT,
  transaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create a notifications table for user notifications
CREATE TABLE public.notifications (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES public.profiles(user_id),
  type TEXT NOT NULL CHECK (type IN ('system', 'financial_move', 'wealth_milestone', 'achievement', 'follow')),
  title TEXT NOT NULL,  
  message TEXT NOT NULL,
  asset_id UUID,
  related_user_id UUID,
  read BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);


-- Create user_assets table for tracking investments and assets
CREATE TABLE public.user_assets (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES public.profiles(user_id),
  asset_type TEXT NOT NULL CHECK (asset_type IN ('stocks', 'property', 'retirement', 'cash', 'bonds', 'crypto')),
  name TEXT NOT NULL,
  value NUMERIC NOT NULL DEFAULT 0,
  quantity NUMERIC DEFAULT 1,
  purchase_price NUMERIC,
  purchase_date TIMESTAMP WITH TIME ZONE DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bank_loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_assets ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for P2P loans
CREATE POLICY "Users can view loans they are involved in" 
ON public.loans 
FOR SELECT 
USING (auth.uid() = lender_id OR auth.uid() = borrower_id);

CREATE POLICY "Users can create loans as lenders" 
ON public.loans 
FOR INSERT 
WITH CHECK (auth.uid() = lender_id);

CREATE POLICY "Users can update loans they are involved in" 
ON public.loans 
FOR UPDATE 
USING (auth.uid() = lender_id OR auth.uid() = borrower_id);

-- Create RLS policies for bank_loans
CREATE POLICY "Users can view bank loans" 
ON public.bank_loans 
FOR SELECT 
USING (true);

CREATE POLICY "Users can borrow bank loans"
ON public.bank_loans 
FOR INSERT 
WITH CHECK (auth.uid() IS NOT NULL);  

CREATE POLICY "Users can pay bank loans"
ON public.bank_loans 
FOR UPDATE 
USING (auth.uid() IS NOT NULL);

-- Create RLS policies for user_balances
CREATE POLICY "Users can view their own balance" 
ON public.user_balances 
FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own balance" 
ON public.user_balances 
FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own balance" 
ON public.user_balances 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Create RLS policies for transactions
CREATE POLICY "Users can view their own transactions" 
ON public.transactions 
FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own transactions" 
ON public.transactions 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own transactions" 
ON public.transactions 
FOR UPDATE 
USING (auth.uid() = user_id);

-- RLS policies for notifications
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own notifications" 
ON public.notifications 
FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own notifications" 
ON public.notifications 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Create RLS policies for user_assets
CREATE POLICY "Users can view their own assets" 
ON public.user_assets 
FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own assets" 
ON public.user_assets 
FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own assets" 
ON public.user_assets 
FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own assets" 
ON public.user_assets 
FOR DELETE 
USING (auth.uid() = user_id);

-- Create triggers for timestamp updates
CREATE TRIGGER update_loans_updated_at
BEFORE UPDATE ON public.loans
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_user_assets_updated_at
BEFORE UPDATE ON public.user_assets
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_balances_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER update_user_balances_updated_at
  BEFORE UPDATE ON public.user_balances
  FOR EACH ROW
  EXECUTE FUNCTION update_user_balances_updated_at();