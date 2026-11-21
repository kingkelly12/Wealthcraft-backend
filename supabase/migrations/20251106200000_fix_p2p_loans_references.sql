-- Enable RLS for p2p_loans table
ALTER TABLE public.p2p_loans ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Users can view available loans" ON public.p2p_loans;
DROP POLICY IF EXISTS "Users can view their own loans" ON public.p2p_loans;
DROP POLICY IF EXISTS "Users can create loans" ON public.p2p_loans;
DROP POLICY IF EXISTS "Users can update their own loans" ON public.p2p_loans;

-- Create policies for p2p_loans table
CREATE POLICY "Users can view available loans" 
ON public.p2p_loans 
FOR SELECT 
TO authenticated 
USING (
  status = 'pending' OR -- Anyone can see pending (available) loans
  lender_id = auth.uid() OR -- Lender can see their own loans
  borrower_id = auth.uid() -- Borrower can see loans they've taken
);

CREATE POLICY "Users can create loans" 
ON public.p2p_loans 
FOR INSERT 
TO authenticated 
WITH CHECK (
  lender_id = auth.uid() -- Only the lender can create their own loans
);

CREATE POLICY "Users can update their own loans" 
ON public.p2p_loans 
FOR UPDATE 
TO authenticated 
USING (
  lender_id = auth.uid() OR -- Lender can update their loans
  borrower_id = auth.uid() -- Borrower can update loans they've taken
)
WITH CHECK (
  lender_id = auth.uid() OR -- Lender can update their loans
  borrower_id = auth.uid() -- Borrower can update loans they've taken
);

-- Add a comment explaining the policies
COMMENT ON TABLE public.p2p_loans IS 'Table for P2P lending marketplace with the following RLS policies:
- Users can view all available (pending) loans
- Users can view their own loans (as lender or borrower)
- Users can create loans (as lender)
- Users can update their own loans (as lender or borrower)';