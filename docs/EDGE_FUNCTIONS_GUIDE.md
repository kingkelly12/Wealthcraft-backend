# Edge Functions Integration Guide

## Overview

You have 3 Edge Functions deployed:
1. **daily-mentor-analysis** - Sends personalized financial advice
2. **daily-volatility** - Updates stock/crypto prices daily
3. **monthly-appreciation** - Appreciates assets based on ROI monthly

## Setup Steps

### 1. Create Database Functions

Run this SQL in Supabase Dashboard → SQL Editor:

```sql
-- Copy contents of: supabase/migrations/20250126_appreciation_functions.sql
```

This creates:
- `get_users_for_appreciation()` - Gets users with appreciating assets
- `apply_monthly_asset_appreciation(user_id)` - Calculates and applies appreciation

### 2. Schedule Edge Functions

Go to Supabase Dashboard → Database → Cron Jobs

#### Daily Volatility (Every day at 12 AM UTC)

**Using Supabase Dashboard Cron Jobs UI:**
- Name: `daily-volatility-update`
- Schedule: `0 0 * * *` (Midnight UTC)
- SQL Command:
```sql
SELECT net.http_post(
  url := 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-volatility',
  headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_ANON_KEY"}'::jsonb
) as request_id;
```

**OR using SQL directly:**
```sql
SELECT cron.schedule(
  'daily-volatility-update',
  '0 0 * * *',
  $$
    SELECT net.http_post(
      url := 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-volatility',
      headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_ANON_KEY"}'::jsonb
    ) as request_id;
  $$
);
```



#### Daily Mentor Analysis (Every day at 9 AM UTC)

**Using Supabase Dashboard Cron Jobs UI:**
- Name: `daily-mentor-analysis`
- Schedule: `0 9 * * *` (9 AM UTC)
- SQL Command:
```sql
SELECT net.http_post(
  url := 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-mentor-analysis',
  headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_SERVICE_ROLE_KEY"}'::jsonb
) as request_id;
```

**OR using SQL directly:**
```sql
SELECT cron.schedule(
  'daily-mentor-analysis',
  '0 9 * * *',
  $$
    SELECT net.http_post(
      url := 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-mentor-analysis',
      headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_SERVICE_ROLE_KEY"}'::jsonb
    ) as request_id;
  $$
);

#### Monthly Loan Deductions (Every day at 2 AM UTC)

**Using Supabase Dashboard Cron Jobs UI:**
- Name: `monthly-loan-deductions`
- Schedule: `0 2 * * *` (2 AM UTC)
- SQL Command:
```sql
SELECT net.http_post(
  url := 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/monthly-loan-deductions',
  headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_SERVICE_ROLE_KEY"}'::jsonb
) as request_id;
```

**OR using SQL directly:**
```sql
SELECT cron.schedule(
  'monthly-loan-deductions',
  '0 2 * * *',
  $$
    SELECT net.http_post(
      url := 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/monthly-loan-deductions',
      headers := '{"Content-Type": "application/json", "Authorization": "Bearer YOUR_SERVICE_ROLE_KEY"}'::jsonb
    ) as request_id;
  $$
);
```
```

### 3. Update Assets Table Schema

Ensure your `assets` table has these columns for volatility:

```sql
ALTER TABLE assets 
ADD COLUMN IF NOT EXISTS previous_price NUMERIC(15, 2),
ADD COLUMN IF NOT EXISTS price_change NUMERIC(15, 2),
ADD COLUMN IF NOT EXISTS price_change_percent NUMERIC(8, 4);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category);
CREATE INDEX IF NOT EXISTS idx_assets_updated_at ON assets(updated_at DESC);
```

### 4. Mobile App Integration

#### Install useAssetPrices Hook

The hook is already created at: `mobile/hooks/useAssetPrices.tsx`

#### Use in Your Marketplace Component

```typescript
import { useAssetPrices } from '@/hooks/useAssetPrices';

export default function MarketplaceScreen() {
  const { assets, volatileAssets, loading, getPriceChange } = useAssetPrices();

  return (
    <View>
      {volatileAssets.map((asset) => {
        const priceChange = getPriceChange(asset);
        
        return (
          <View key={asset.id}>
            <Text>{asset.name}</Text>
            <Text>${asset.price.toFixed(2)}</Text>
            <Text className={priceChange.isPositive ? 'text-green-600' : 'text-red-600'}>
              {priceChange.isPositive ? '+' : ''}{priceChange.percent.toFixed(2)}%
            </Text>
          </View>
        );
      })}
    </View>
  );
}
```

## How Each Function Works

### Daily Volatility

**What it does:**
- Runs every day at midnight
- Updates prices for stocks and crypto
- Crypto: -12% to +15% daily volatility
- Stocks: -7% to +8% daily volatility
- Stores previous price and change percentage

**Database updates:**
```sql
UPDATE assets
SET 
  previous_price = price,
  price = new_price,
  price_change = change_amount,
  price_change_percent = change_percent,
  updated_at = NOW()
WHERE category IN ('stocks', 'crypto');
```

**Mobile app sees:**
- Real-time price updates via Supabase subscriptions
- Price change indicators (green/red)
- Percentage changes

### Monthly Appreciation

**What it does:**
- Runs on 1st of every month
- Appreciates non-volatile assets (real estate, bonds, etc.)
- Based on annual ROI divided by 12
- Creates notifications for significant gains
- Updates user net worth

**Example:**
- Asset: Rental Property
- Current Value: $100,000
- Annual ROI: 6%
- Monthly Appreciation: $100,000 × (6% / 12) = $500
- New Value: $100,500

**Notifications created:**
- Individual asset appreciation >$100 AND >1%
- Total portfolio growth >$1,000

### Daily Mentor Analysis

**What it does:**
- Analyzes player financial metrics
- Checks trigger conditions
- Sends personalized advice
- Awards points for following advice

**Triggers:**
- High cash ratio, high debt, poor diversification, etc.
- See implementation_plan.md for full list

## Testing

### Test Volatility Function
```bash
curl -X POST 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-volatility' \
  -H 'Authorization: Bearer YOUR_ANON_KEY'
```

### Test Appreciation Function
```bash
curl -X POST 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/monthly-appreciation' \
  -H 'Authorization: Bearer YOUR_SERVICE_ROLE_KEY'
```

### Test Mentor Function
```bash
curl -X POST 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-mentor-analysis' \
  -H 'Authorization: Bearer YOUR_SERVICE_ROLE_KEY'
```

## Monitoring

### Check Cron Jobs
```sql
SELECT * FROM cron.job;
SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;
```

### Check Function Logs
- Supabase Dashboard → Edge Functions → Select function → Logs

### Check Asset Updates
```sql
-- Recent price changes
SELECT 
  name, 
  category,
  price, 
  previous_price,
  price_change_percent,
  updated_at
FROM assets
WHERE category IN ('stocks', 'crypto')
ORDER BY updated_at DESC
LIMIT 20;
```

### Check Appreciations
```sql
-- Recent appreciations
SELECT 
  ua.user_id,
  a.name,
  ua.value,
  ua.updated_at
FROM user_assets ua
JOIN assets a ON ua.asset_id = a.id
WHERE a.category NOT IN ('stocks', 'crypto')
ORDER BY ua.updated_at DESC
LIMIT 20;
```

## Troubleshooting

### Volatility not updating
- Check cron job is active
- Verify ANON_KEY is set
- Check function logs for errors
- Ensure assets table has required columns

### Appreciation not working
- Verify database functions exist
- Check SERVICE_ROLE_KEY is set
- Ensure users have assets with ROI > 0
- Check function logs

### No notifications
- Verify notifications table exists
- Check user_id matches
- Ensure notification preferences allow

## Mobile App Checklist

- [ ] useAssetPrices hook created
- [ ] Marketplace component uses real-time prices
- [ ] Price change indicators (green/red arrows)
- [ ] Percentage change display
- [ ] Asset detail page shows price history
- [ ] Notifications for appreciation
- [ ] Mentor messages displayed

## Next Steps

1. Run database migration for appreciation functions
2. Set up cron jobs for all 3 functions
3. Update assets table schema
4. Integrate useAssetPrices in marketplace
5. Test each function manually
6. Monitor logs for 24 hours
7. Verify mobile app shows real-time updates
