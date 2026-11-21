// Supabase Edge Function for Monthly Liability Depreciation
// Deploy with: supabase functions deploy monthly-depreciation
// Called by: Supabase Cron Job (scheduled monthly)

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

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
        console.log('🚀 Starting monthly liability depreciation job...')

        // Get Flask backend URL from environment
        const flaskUrl = Deno.env.get('FLASK_API_URL')
        if (!flaskUrl) {
            throw new Error('FLASK_API_URL environment variable not set')
        }

        // Call Flask endpoint for monthly depreciation
        const response = await fetch(
            `${flaskUrl}/api/liabilities/cron/monthly-depreciation`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`
                }
            }
        )

        if (!response.ok) {
            const errorData = await response.text()
            console.error(`❌ Flask endpoint error (${response.status}):`, errorData)
            throw new Error(`Flask API error: ${response.status} - ${errorData}`)
        }

        const result = await response.json()

        console.log('✅ Monthly depreciation job completed successfully')
        console.log(`📊 Backfilled: ${result.backfilled || 0} liabilities`)
        console.log(`📉 Updated: ${result.updated || 0} liabilities`)
        console.log(`💰 Total depreciation: $${(result.total_depreciation || 0).toFixed(2)}`)
        console.log(`📅 Date: ${result.date}`)

        return new Response(
            JSON.stringify({
                success: true,
                message: 'Monthly depreciation job completed',
                data: result
            }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 200,
            }
        )

    } catch (error) {
        console.error('💥 Error in monthly depreciation job:', error)

        return new Response(
            JSON.stringify({
                success: false,
                error: (error as Error).message
            }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 400,
            }
        )
    }
})
