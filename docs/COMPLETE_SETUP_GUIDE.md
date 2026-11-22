# Complete Setup Guide - Mentor System & Mobile App

## Part 1: Deploy Edge Function to Supabase

### Option A: Using Supabase CLI (Recommended)

```bash
# 1. Install Supabase CLI
npm install -g supabase

# 2. Login to Supabase
supabase login

# 3. Link your project
cd /home/kelly_koome/Devops/wealthcraft-legacy-sim
supabase link --project-ref lllydwymcuulrsqxumvl

# 4. Deploy the function
supabase functions deploy daily-mentor-analysis

# 5. Set up secrets (environment variables)
supabase secrets set SUPABASE_URL=https://lllydwymcuulrsqxumvl.supabase.co
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# 6. Schedule the function (run daily at 9 AM)
# Go to Supabase Dashboard → Database → Cron Jobs
# Add new cron job:
# Schedule: 0 9 * * *
# Function: daily-mentor-analysis
```

### Option B: Manual Deployment via Dashboard

1. **Go to Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard/project/lllydwymcuulrsqxumvl

2. **Create Edge Function**
   - Click "Edge Functions" in sidebar
   - Click "Create a new function"
   - Name: `daily-mentor-analysis`

3. **Copy Code**
   - Open: `supabase/functions/daily-mentor-analysis/index.ts`
   - Copy all contents
   - Paste into the function editor

4. **Set Environment Variables**
   - Click "Settings" tab
   - Add secrets:
     - `SUPABASE_URL`: https://lllydwymcuulrsqxumvl.supabase.co
     - `SUPABASE_SERVICE_ROLE_KEY`: (get from Settings → API)

5. **Deploy**
   - Click "Deploy function"

6. **Schedule Execution**
   - Go to Database → Cron Jobs
   - Click "Create a new cron job"
   - Schedule: `0 9 * * *` (9 AM daily)
   - SQL Command:
   ```sql
   SELECT
     net.http_post(
       url:='https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-mentor-analysis',
       headers:='{"Content-Type": "application/json", "Authorization": "Bearer YOUR_ANON_KEY"}'::jsonb
     ) as request_id;
   ```

### Test the Function

```bash
# Using curl
curl -X POST 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-mentor-analysis' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json'
```

---

## Part 2: Install Mobile App on Android

### Quick Start (Easiest - 2 minutes)

```bash
# 1. Install Expo Go on your Android phone
# - Open Play Store
# - Search "Expo Go"
# - Install

# 2. Start development server
cd /home/kelly_koome/Devops/wealthcraft-legacy-sim/mobile
npx expo start

# 3. Scan QR code with Expo Go
# - Open Expo Go app
# - Tap "Scan QR Code"
# - Point camera at QR code in terminal
# - App will load on your phone
```

### Production Build (Full Features)

```bash
# 1. Install EAS CLI
npm install -g eas-cli

# 2. Login to Expo
eas login

# 3. Configure project
cd /home/kelly_koome/Devops/wealthcraft-legacy-sim/mobile
eas build:configure

# 4. Build APK
eas build --profile production --platform android

# 5. Wait for build (10-20 minutes)
# You'll get a download link

# 6. Download APK to your computer

# 7. Transfer to phone
# - Connect phone via USB
# - Copy APK to phone storage
# OR
# - Upload to Google Drive
# - Download on phone

# 8. Install on phone
# - Open APK file on phone
# - Allow "Install from Unknown Sources"
# - Tap Install
```

### Development Build (For Testing with Hot Reload)

```bash
# 1. Create development build
eas build --profile development --platform android

# 2. Install APK on phone

# 3. Start dev server
npx expo start --dev-client

# 4. Open app on phone
# - It will connect to dev server
# - Changes will hot-reload
```

---

## Part 3: Run Database Migrations

### Create Mentor Tables

The mentor tables (`mentors`, `mentor_messages`, `player_mentor_interactions`)
are created by `supabase/schema.sql`. Nothing extra to run.

### Seed Mentor Data

**Supabase Dashboard:**
1. Go to SQL Editor
2. Copy contents of: `supabase/seed_mentors.sql`
3. Paste and click "Run"

---

## Part 4: Verify Everything Works

### 1. Check Database
```sql
-- Run in Supabase SQL Editor
SELECT COUNT(*) FROM mentors; -- Should return 3
SELECT COUNT(*) FROM mentor_messages; -- Should return 12
```

### 2. Test Edge Function
```bash
# Trigger manually
curl -X POST 'https://lllydwymcuulrsqxumvl.supabase.co/functions/v1/daily-mentor-analysis' \
  -H 'Authorization: Bearer YOUR_ANON_KEY'
```

### 3. Check Mobile App
1. Open app on phone
2. Navigate to Mentors screen
3. Should see 3 mentors
4. Check for any messages

---

## Troubleshooting

### Edge Function Issues

**"Module could not be parsed" error:**
- ✅ Fixed! Use the TypeScript version in `supabase/functions/daily-mentor-analysis/index.ts`

**Function not executing:**
- Check cron job is active
- Verify environment variables are set
- Check function logs in Dashboard

### Mobile App Issues

**Can't connect to dev server:**
- Ensure phone and computer on same WiFi
- Try: `npx expo start --tunnel`

**App crashes on startup:**
- Check Supabase connection in `src/integrations/supabase/client.ts`
- Verify API keys are correct

**Build fails:**
- Clear cache: `npx expo start -c`
- Reinstall: `rm -rf node_modules && npm install`

### Database Issues

**Tables not created:**
- Check migration SQL for errors
- Verify you have admin permissions
- Try creating tables one by one

**Seed data fails:**
- Ensure tables exist first
- Check for UUID conflicts
- Verify foreign key constraints

---

## Quick Reference

### Important Files
- Edge Function: `supabase/functions/daily-mentor-analysis/index.ts`
- Tables: `supabase/schema.sql`
- Seed Data: `supabase/seed_mentors.sql`
- Mobile Setup: `mobile/ANDROID_INSTALL.md`

### Important Commands
```bash
# Deploy Edge Function
supabase functions deploy daily-mentor-analysis

# Start mobile dev server
npx expo start

# Build production APK
eas build --profile production --platform android

# Test Edge Function
curl -X POST 'https://[PROJECT].supabase.co/functions/v1/daily-mentor-analysis' \
  -H 'Authorization: Bearer [KEY]'
```

### Important URLs
- Supabase Dashboard: https://supabase.com/dashboard/project/lllydwymcuulrsqxumvl
- Edge Functions: https://supabase.com/dashboard/project/lllydwymcuulrsqxumvl/functions
- SQL Editor: https://supabase.com/dashboard/project/lllydwymcuulrsqxumvl/sql
- Cron Jobs: https://supabase.com/dashboard/project/lllydwymcuulrsqxumvl/database/cron-jobs
