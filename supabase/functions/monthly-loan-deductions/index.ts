
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req: Request) => {
    // Handle CORS preflight requests
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const supabase = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        )

        console.log('Starting monthly loan deduction job...')

        // 1. Fetch all active bank loans
        const { data: loans, error: loansError } = await supabase
            .from('bank_loans')
            .select('*')
            .eq('status', 'active')

        if (loansError) {
            console.error('Error fetching loans:', loansError)
            throw loansError
        }

        console.log(`Found ${loans?.length || 0} active loans`)

        let processedCount = 0
        let errorCount = 0

        for (const loan of loans || []) {
            try {
                // 2. Get user's current balance
                const { data: balanceRecord, error: balanceError } = await supabase
                    .from('user_balances')
                    .select('current_balance')
                    .eq('user_id', loan.borrower_id)
                    .single()

                if (balanceError) {
                    console.error(`Error fetching balance for user ${loan.borrower_id}:`, balanceError)
                    errorCount++
                    continue
                }

                const currentBalance = parseFloat(balanceRecord.current_balance)
                const monthlyPayment = parseFloat(loan.monthly_payment)

                // 3. Check if sufficient funds
                if (currentBalance >= monthlyPayment) {
                    const newBalance = currentBalance - monthlyPayment

                    // 4. Update balance
                    const { error: updateError } = await supabase
                        .from('user_balances')
                        .update({
                            current_balance: newBalance,
                            updated_at: new Date().toISOString()
                        })
                        .eq('user_id', loan.borrower_id)

                    if (updateError) {
                        throw updateError
                    }

                    // 5. Record Transaction
                    const { error: txError } = await supabase
                        .from('transactions')
                        .insert({
                            user_id: loan.borrower_id,
                            type: 'loan_payment',
                            category: 'Debt',
                            amount: monthlyPayment,
                            description: `Monthly payment for ${loan.type} loan`
                        })

                    if (txError) {
                        console.error(`Error recording transaction for user ${loan.borrower_id}:`, txError)
                        // Non-critical, but good to know
                    }

                    console.log(`Successfully processed payment of $${monthlyPayment} for user ${loan.borrower_id}`)
                    processedCount++

                } else {
                    console.log(`User ${loan.borrower_id} has insufficient funds ($${currentBalance}) for payment of $${monthlyPayment}`)

                    // Optional: Create a notification for missed payment
                    await supabase
                        .from('notifications')
                        .insert({
                            user_id: loan.borrower_id,
                            type: 'system',
                            title: 'Loan Payment Failed',
                            message: `Insufficient funds for your ${loan.type} loan payment of $${monthlyPayment}.`,
                            read: false
                        })
                }

            } catch (err) {
                console.error(`Error processing loan ${loan.id}:`, err)
                errorCount++
            }
        }

        return new Response(
            JSON.stringify({
                success: true,
                processed: processedCount,
                errors: errorCount
            }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 200,
            }
        )

    } catch (error) {
        return new Response(
            JSON.stringify({ error: (error as Error).message }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 400,
            }
        )
    }
})
