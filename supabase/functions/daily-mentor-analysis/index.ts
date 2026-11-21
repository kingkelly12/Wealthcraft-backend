// Supabase Edge Function for Daily Mentor Analysis
// Deploy with: supabase functions deploy daily-mentor-analysis

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface PlayerMetrics {
    net_worth: number;
    total_assets: number;
    total_liabilities: number;
    cash: number;
    cash_ratio: number;
    monthly_income: number;
    monthly_debt_payments: number;
    debt_to_income_ratio: number;
    asset_concentration: number;
}

interface Trigger {
    type: string;
    mentor_role: string;
    priority: number;
    data: Record<string, any>;
}

serve(async (req) => {
    // Handle CORS preflight requests
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const supabaseClient = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        )

        console.log('Starting daily mentor analysis...')

        // Get active users (logged in within last 30 days)
        const thirtyDaysAgo = new Date()
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

        const { data: activeUsers, error: usersError } = await supabaseClient
            .from('users')
            .select('id')
            .gte('last_login', thirtyDaysAgo.toISOString())

        if (usersError) throw usersError

        console.log(`Found ${activeUsers?.length || 0} active users`)

        let messagesSent = 0
        let errors = 0

        for (const user of activeUsers || []) {
            try {
                // Get profile
                const { data: profile } = await supabaseClient
                    .from('profiles')
                    .select('*')
                    .eq('user_id', user.id)
                    .single()

                if (!profile) continue

                // Analyze finances
                const metrics = await analyzePlayerFinances(supabaseClient, user.id)
                if (!metrics) continue

                // Check triggers
                const triggers = checkTriggers(metrics)

                // Sort by priority
                triggers.sort((a, b) => b.priority - a.priority)

                // Send top 1-2 messages
                for (const trigger of triggers.slice(0, 2)) {
                    const mentorData = await generatePersonalizedMessage(
                        supabaseClient,
                        trigger,
                        profile.username
                    )

                    if (mentorData) {
                        await sendMentorMessage(
                            supabaseClient,
                            user.id,
                            mentorData,
                            metrics
                        )
                        messagesSent++
                        console.log(`Sent ${trigger.type} message to ${profile.username}`)
                    }
                }
            } catch (error) {
                errors++
                console.error(`Error processing user ${user.id}:`, error)
            }
        }

        console.log(`Analysis complete. Messages: ${messagesSent}, Errors: ${errors}`)

        return new Response(
            JSON.stringify({
                success: true,
                messages_sent: messagesSent,
                errors: errors,
                users_processed: activeUsers?.length || 0
            }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 200,
            },
        )
    } catch (error) {
        return new Response(
            JSON.stringify({ error: error.message }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 400,
            },
        )
    }
})

async function analyzePlayerFinances(supabase: any, playerId: string): Promise<PlayerMetrics | null> {
    try {
        // Get profile
        const { data: profile } = await supabase
            .from('profiles')
            .select('*')
            .eq('user_id', playerId)
            .single()

        if (!profile) return null

        // Get assets
        const { data: assets } = await supabase
            .from('user_assets')
            .select('*')
            .eq('user_id', playerId)

        const totalAssets = assets?.reduce((sum: number, a: any) => sum + parseFloat(a.value || 0), 0) || 0

        // Get liabilities
        const { data: liabilities } = await supabase
            .from('liabilities')
            .select('*')
            .eq('user_id', playerId)

        const totalLiabilities = liabilities?.reduce((sum: number, l: any) => sum + parseFloat(l.amount || 0), 0) || 0
        const monthlyDebt = liabilities?.reduce((sum: number, l: any) => sum + parseFloat(l.monthly_payment || 0), 0) || 0

        // Get balance
        const { data: balance } = await supabase
            .from('user_balances')
            .select('*')
            .eq('user_id', playerId)
            .single()

        const cash = parseFloat(balance?.current_balance || 0)

        // Calculate metrics
        const netWorth = parseFloat(profile.net_worth || 0)
        const monthlyIncome = parseFloat(profile.monthly_income || 0)

        // Asset concentration
        const assetTypes: Record<string, number> = {}
        assets?.forEach((asset: any) => {
            const type = asset.asset_type || 'other'
            assetTypes[type] = (assetTypes[type] || 0) + parseFloat(asset.value || 0)
        })

        const maxConcentration = totalAssets > 0
            ? Math.max(...Object.values(assetTypes)) / totalAssets
            : 0

        return {
            net_worth: netWorth,
            total_assets: totalAssets,
            total_liabilities: totalLiabilities,
            cash: cash,
            cash_ratio: totalAssets > 0 ? cash / totalAssets : 0,
            monthly_income: monthlyIncome,
            monthly_debt_payments: monthlyDebt,
            debt_to_income_ratio: monthlyIncome > 0 ? monthlyDebt / monthlyIncome : 0,
            asset_concentration: maxConcentration,
        }
    } catch (error) {
        console.error('Error analyzing finances:', error)
        return null
    }
}

function checkTriggers(metrics: PlayerMetrics): Trigger[] {
    const triggers: Trigger[] = []

    // High cash ratio (>50%)
    if (metrics.cash_ratio > 0.5) {
        triggers.push({
            type: 'high_cash_ratio',
            mentor_role: 'strategic',
            priority: 4,
            data: {
                cash_amount: Math.round(metrics.cash),
                cash_percentage: Math.round(metrics.cash_ratio * 100),
                inflation_loss: Math.round(metrics.cash * 0.03)
            }
        })
    }

    // High debt-to-income (>40%)
    if (metrics.debt_to_income_ratio > 0.4) {
        triggers.push({
            type: 'high_debt_to_income',
            mentor_role: 'risk_analyst',
            priority: 5,
            data: {
                debt_percentage: Math.round(metrics.debt_to_income_ratio * 100),
                monthly_debt: Math.round(metrics.monthly_debt_payments)
            }
        })
    }

    // Net worth milestones
    if (metrics.net_worth >= 10000 && metrics.net_worth < 15000) {
        triggers.push({
            type: 'milestone_10k',
            mentor_role: 'emotional',
            priority: 3,
            data: { net_worth: Math.round(metrics.net_worth) }
        })
    }

    // Poor diversification (>70%)
    if (metrics.asset_concentration > 0.7) {
        triggers.push({
            type: 'poor_diversification',
            mentor_role: 'strategic',
            priority: 4,
            data: { concentration: Math.round(metrics.asset_concentration * 100) }
        })
    }

    return triggers
}

async function generatePersonalizedMessage(
    supabase: any,
    trigger: Trigger,
    username: string
): Promise<any> {
    // Get mentor by role
    const { data: mentor } = await supabase
        .from('mentors')
        .select('*')
        .eq('role', trigger.mentor_role)
        .single()

    if (!mentor) return null

    // Get message template
    const { data: template } = await supabase
        .from('mentor_messages')
        .select('*')
        .eq('mentor_id', mentor.id)
        .eq('trigger_type', trigger.type)
        .eq('is_active', true)
        .single()

    if (!template) return null

    // Personalize message
    let personalizedMessage = template.message_template
    personalizedMessage = personalizedMessage.replace('{username}', username)

    // Replace all data placeholders
    for (const [key, value] of Object.entries(trigger.data)) {
        const regex = new RegExp(`\\{${key}(:,)?\\}`, 'g')
        personalizedMessage = personalizedMessage.replace(regex, value.toString())
    }

    return {
        mentor,
        template,
        personalized_message: personalizedMessage,
        trigger_data: trigger.data
    }
}

async function sendMentorMessage(
    supabase: any,
    playerId: string,
    mentorData: any,
    metrics: PlayerMetrics
) {
    const { error } = await supabase
        .from('player_mentor_interactions')
        .insert({
            player_id: playerId,
            mentor_id: mentorData.mentor.id,
            message_id: mentorData.template.id,
            message_content: mentorData.personalized_message,
            trigger_type: mentorData.template.trigger_type,
            player_data_snapshot: metrics
        })

    if (error) throw error
}
