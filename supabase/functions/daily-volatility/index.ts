import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.4'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    // Fetch only stocks and crypto assets
    const { data: assets, error: fetchError } = await supabaseClient
      .from('assets')
      .select('*')
      .in('category', ['stocks', 'crypto'])

    if (fetchError) throw fetchError

    const updates = assets.map(asset => {
      // Different volatility for stocks vs crypto
      let volatilityRange: [number, number]
      
      if (asset.category === 'crypto') {
        // Crypto: -12% to +15% daily
        volatilityRange = [-0.12, 0.15]
      } else {
        // Stocks: -7% to +8% daily
        volatilityRange = [-0.07, 0.08]
      }

      // Generate random price change
      const changePercent = (Math.random() * (volatilityRange[1] - volatilityRange[0])) + volatilityRange[0]
      const change = asset.price * changePercent
      const newPrice = Math.max(0.01, asset.price + change) // Prevent negative prices

      return {
        id: asset.id,
        previous_price: asset.price,
        price: newPrice,
        price_change: change,
        price_change_percent: changePercent * 100,
        updated_at: new Date().toISOString(),
      }
    })

    // Batch update all assets
    const { error: updateError } = await supabaseClient
      .from('assets')
      .upsert(updates)

    if (updateError) throw updateError

    return new Response(
      JSON.stringify({ 
        success: true, 
        updated: updates.length,
        message: `Updated ${updates.length} volatile assets`
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400 
      }
    )
  }
})