-- Add transaction management functions
CREATE OR REPLACE FUNCTION begin_p2p_transaction()
RETURNS void
SECURITY DEFINER
LANGUAGE plpgsql AS $$
BEGIN
  -- Start a transaction
  BEGIN;
END;
$$;

CREATE OR REPLACE FUNCTION commit_p2p_transaction()
RETURNS void
SECURITY DEFINER
LANGUAGE plpgsql AS $$
BEGIN
  -- Commit the transaction
  COMMIT;
END;
$$;

CREATE OR REPLACE FUNCTION rollback_p2p_transaction()
RETURNS void
SECURITY DEFINER
LANGUAGE plpgsql AS $$
BEGIN
  -- Rollback the transaction
  ROLLBACK;
END;
$$;

-- Create a function to process P2P loan application
CREATE OR REPLACE FUNCTION process_p2p_loan_application(
  p_loan_id UUID,
  p_borrower_id UUID,
  p_amount NUMERIC,
  p_purpose TEXT
)
RETURNS json
SECURITY DEFINER
LANGUAGE plpgsql AS $$
DECLARE
  v_lender_id UUID;
  v_loan_record RECORD;
  v_borrower_balance NUMERIC;
  v_lender_balance NUMERIC;
BEGIN
  -- Get loan details
  SELECT * INTO v_loan_record
  FROM p2p_loans
  WHERE id = p_loan_id AND status = 'pending';
  
  IF v_loan_record IS NULL THEN
    RETURN json_build_object('success', false, 'message', 'Loan not found or not available');
  END IF;
  
  v_lender_id := v_loan_record.lender_id;
  
  -- Get balances
  SELECT current_balance INTO v_lender_balance
  FROM user_balances
  WHERE user_id = v_lender_id;
  
  IF v_lender_balance < p_amount THEN
    RETURN json_build_object('success', false, 'message', 'Insufficient lender balance');
  END IF;
  
  -- Begin transaction
  BEGIN;
    -- Update loan status
    UPDATE p2p_loans
    SET 
      status = 'active',
      borrower_id = p_borrower_id,
      funded_at = NOW()
    WHERE id = p_loan_id;
    
    -- Transfer funds from lender to borrower
    UPDATE user_balances
    SET current_balance = current_balance - p_amount
    WHERE user_id = v_lender_id;
    
    UPDATE user_balances
    SET current_balance = current_balance + p_amount
    WHERE user_id = p_borrower_id;
    
    -- Record transactions
    INSERT INTO transactions (user_id, type, category, amount, description)
    VALUES
      (v_lender_id, 'expense', 'p2p_loan_given', -p_amount, 'P2P Loan given: ' || p_purpose),
      (p_borrower_id, 'income', 'p2p_loan_received', p_amount, 'P2P Loan received: ' || p_purpose);
    
    -- Create notifications
    INSERT INTO notifications (user_id, type, title, message, read)
    VALUES
      (v_lender_id, 'financial_move', 'Loan Funded', 
       'Your loan offer of $' || p_amount || ' has been accepted and funded.', false),
      (p_borrower_id, 'financial_move', 'Loan Received', 
       'You have received a loan of $' || p_amount || '.', false);
    
    COMMIT;
    
    RETURN json_build_object('success', true, 'message', 'Loan processed successfully');
  EXCEPTION WHEN OTHERS THEN
    ROLLBACK;
    RETURN json_build_object('success', false, 'message', 'Transaction failed: ' || SQLERRM);
  END;
END;
$$;