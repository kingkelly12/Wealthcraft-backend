import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

const supabase = createClient(supabaseUrl, supabaseServiceKey)

interface AssetAppreciation {
  asset_id: string
  asset_name: string
  previous_value: number
  new_value: number
  appreciation_amount: number
  appreciation_percent: number
}

serve(async (req) => {
  try {
    console.log('🚀 Starting monthly asset appreciation process...')

    // Get all users that need appreciation processing
    const { data: users, error: usersError } = await supabase.rpc('get_users_for_appreciation')

    if (usersError) {
      console.error('❌ Error fetching users:', usersError)
      return new Response(JSON.stringify({ error: usersError }), { status: 500 })
    }

    console.log(`📊 Processing ${users?.length || 0} users for asset appreciation`)

    let totalProcessed = 0
    let totalNotificationsCreated = 0

    // Process appreciation for each user
    for (const user of users || []) {
      try {
        console.log(`⏳ Processing user: ${user.user_id}`)

        // Call the appreciation function
        const { data: appreciations, error: appreciationError } = await supabase.rpc(
          'apply_monthly_asset_appreciation',
          { user_id_param: user.user_id }
        )

        if (appreciationError) {
          console.error(`❌ Error processing appreciation for user ${user.user_id}:`, appreciationError)
          continue
        }

        const appData = appreciations as AssetAppreciation[]

        // Create notifications for significant appreciations
        for (const appreciation of appData || []) {
          // Only notify for appreciations over $100 AND over 1%
          if (appreciation.appreciation_amount > 100 && appreciation.appreciation_percent > 1) {
            const { error: notifError } = await supabase
              .from('notifications')
              .insert({
                user_id: user.user_id,
                type: 'financial_move',
                title: 'Asset Appreciated!',
                message: `${appreciation.asset_name} increased by $${appreciation.appreciation_amount.toFixed(2)} (${appreciation.appreciation_percent.toFixed(2)}%) this month`,
                read: false
              })

            if (!notifError) {
              totalNotificationsCreated++
            }
          }
        }

        // Update user's net worth
        if (appData && appData.length > 0) {
          const totalAppreciation = appData.reduce((sum, app) => sum + app.appreciation_amount, 0)

          if (totalAppreciation > 1000) {
            await supabase
              .from('notifications')
              .insert({
                user_id: user.user_id,
                type: 'wealth_milestone',
                title: 'Portfolio Growth',
                message: `Your portfolio grew by $${totalAppreciation.toFixed(2)} this month!`,
                read: false
              })
            totalNotificationsCreated++
          }

          // Update profile net worth (you'll need to implement this based on your schema)
          console.log(`✅ Processed ${appData.length} appreciating assets for user ${user.user_id}`)
          totalProcessed++
        }
      } catch (userError) {
        console.error(`💥 Error processing user ${user.user_id}:`, userError)
      }
    }

    console.log(`🎉 Monthly asset appreciation complete!`)
    console.log(`📈 Users processed: ${totalProcessed}`)
    console.log(`🔔 Notifications created: ${totalNotificationsCreated}`)

    return new Response(
      JSON.stringify({
        success: true,
        usersProcessed: totalProcessed,
        notificationsCreated: totalNotificationsCreated
      }),
      {
        headers: { 'Content-Type': 'application/json' },
        status: 200
      }
    )
  } catch (err) {
    console.error('💥 Unexpected error:', err)
    return new Response(JSON.stringify({ error: err.message }), { status: 500 })
  }
})
