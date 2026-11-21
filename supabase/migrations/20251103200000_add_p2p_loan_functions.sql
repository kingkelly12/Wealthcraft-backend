-- ✅ Create a function to process P2P loan applications
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
  -- 🔹 Get loan details
  SELECT * INTO v_loan_record
  FROM p2p_loans
  WHERE id = p_loan_id AND status = 'pending';
  
  IF v_loan_record IS NULL THEN
    RETURN json_build_object('success', false, 'message', 'Loan not found or not available');
  END IF;
  
  v_lender_id := v_loan_record.lender_id;
  
  -- 🔹 Check lender balance
  SELECT current_balance INTO v_lender_balance
  FROM user_balances
  WHERE user_id = v_lender_id;
  
  IF v_lender_balance < p_amount THEN
    RETURN json_build_object('success', false, 'message', 'Insufficient lender balance');
  END IF;
  
  -- 🔹 Try to process the loan safely
  BEGIN
    -- Update loan status
    UPDATE p2p_loans
    SET 
      status = 'active',
      borrower_id = p_borrower_id,
      funded_at = NOW()
    WHERE id = p_loan_id;
    
    -- Deduct funds from lender
    UPDATE user_balances
    SET current_balance = current_balance - p_amount
    WHERE user_id = v_lender_id;
    
    -- Credit borrower
    UPDATE user_balances
    SET current_balance = current_balance + p_amount
    WHERE user_id = p_borrower_id;
    
    -- Record both transactions
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

    RETURN json_build_object('success', true, 'message', 'Loan processed successfully');
  
  EXCEPTION WHEN OTHERS THEN
    -- Rollback automatically happens for function errors
    RETURN json_build_object('success', false, 'message', 'Transaction failed: ' || SQLERRM);
  END;
END;
$$;




-- ✅ Create function to process P2P loan repayments
CREATE OR REPLACE FUNCTION public.process_p2p_loan_repayment(
  p_loan_id UUID,
  p_borrower_id UUID,
  p_lender_id UUID,
  p_amount DECIMAL,
  p_due_date TIMESTAMP
)
RETURNS void AS $$
DECLARE
  v_borrower_balance DECIMAL;
  v_repayment_id UUID;
BEGIN
  -- Check borrower's balance
  SELECT current_balance INTO v_borrower_balance
  FROM user_balances
  WHERE user_id = p_borrower_id;

  IF v_borrower_balance < p_amount THEN
    -- Record missed payment
    UPDATE loan_repayments
    SET status = 'missed',
        payment_date = NOW()
    WHERE loan_id = p_loan_id
      AND due_date = p_due_date
    RETURNING id INTO v_repayment_id;

    -- Create notifications
    INSERT INTO notifications (user_id, type, title, message, read)
    VALUES
      (p_borrower_id, 'financial_move', 'Missed Loan Payment', 
       format('You missed a loan payment of $%s. Please ensure sufficient funds for the next payment.', p_amount::text),
       false),
      (p_lender_id, 'financial_move', 'Borrower Missed Payment',
       format('A borrower missed their payment of $%s.', p_amount::text),
       false);

    -- Record in credit history
    INSERT INTO credit_history (user_id, event_type, amount, description, impact)
    VALUES (p_borrower_id, 'loan_default', p_amount, 'Missed P2P loan payment', -30);

  ELSE
    -- Process successful payment
    UPDATE user_balances
    SET current_balance = current_balance - p_amount
    WHERE user_id = p_borrower_id;

    UPDATE user_balances
    SET current_balance = current_balance + p_amount
    WHERE user_id = p_lender_id;

    UPDATE loan_repayments
    SET status = 'paid',
        payment_date = NOW()
    WHERE loan_id = p_loan_id
      AND due_date = p_due_date
    RETURNING id INTO v_repayment_id;

    INSERT INTO transactions (user_id, type, category, amount, description)
    VALUES
      (p_borrower_id, 'expense', 'loan_payment', -p_amount, 'P2P Loan Payment'),
      (p_lender_id, 'income', 'loan_payment_received', p_amount, 'P2P Loan Payment Received');

    INSERT INTO credit_history (user_id, event_type, amount, description, impact)
    VALUES (p_borrower_id, 'loan_payment', p_amount, 'On-time P2P loan payment', 2);

    INSERT INTO notifications (user_id, type, title, message, read)
    VALUES
      (p_borrower_id, 'financial_move', 'Loan Payment Successful', 
       format('Your loan payment of $%s has been processed.', p_amount::text),
       false),
      (p_lender_id, 'financial_move', 'Loan Payment Received',
       format('You received a loan payment of $%s.', p_amount::text),
       false);
  END IF;
END;
$$ LANGUAGE plpgsql;
