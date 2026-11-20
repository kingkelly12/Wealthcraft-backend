# Expo Push Tokens: Complete Explanation for Junior Developers

## TL;DR (Too Long; Didn't Read)

**What is it?** A unique identifier that lets the backend send notifications to your specific device.

**When is it generated?** When the app calls `Notifications.getExpoPushTokenAsync()` (usually when you open the app).

**How do you get it?** Open the app → Expo library generates it → app sends it to backend → backend saves it in database.

**What happens when you reinstall?** You get a NEW token (old one is invalid), so you need to open the app to register the new one.

---

## The Complete Flow (Beginner Explanation)

Think of push notifications like receiving mail:

- **Your Device** = Your home address
- **Expo Push Token** = A unique mailbox ID (only valid for your device)
- **Backend Server** = The post office
- **Push Notification** = The letter being delivered

### The 4-Step Process

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: App Startup                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User opens app                                                  │
│        ↓                                                         │
│  App code runs:                                                  │
│  const token = await Notifications.getExpoPushTokenAsync()      │
│        ↓                                                         │
│  ✅ Get token from Expo infrastructure                          │
│  Example: "ExponentPushToken[abc123xyz...]"                     │
│        ↓                                                         │
│  Store in memory/state                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: App Registers Token with Backend                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  App sends HTTP POST to backend:                                │
│  /api/notification/register-token/                              │
│                                                                  │
│  Headers:                                                        │
│    Authorization: Bearer {jwt_token}                            │
│    Content-Type: application/json                               │
│                                                                  │
│  Body:                                                           │
│    {                                                             │
│      "push_token": "ExponentPushToken[abc123xyz...]"            │
│    }                                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Backend Saves Token to Database                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Backend code (Python/Flask):                                   │
│                                                                  │
│  # Validate token                                               │
│  if not validate_push_token(data.push_token):                   │
│      return error                                               │
│                                                                  │
│  # Save to database                                             │
│  supabase.table('profiles').update({                            │
│      'expo_push_token': 'ExponentPushToken[abc123...]',         │
│      'push_token_updated_at': '2026-05-20T07:00:00'            │
│  }).eq('user_id', user_id).execute()                           │
│                                                                  │
│  # Return success                                               │
│  return {                                                        │
│      'success': True,                                           │
│      'message': 'Push token registered successfully'            │
│  }                                                               │
│                                                                  │
│  ✅ Token is now in the database!                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Backend Can Now Send Notifications                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Later, when something happens (life event, etc.):              │
│                                                                  │
│  # Get token from database                                      │
│  token = supabase.table('profiles')                             │
│      .select('expo_push_token')                                 │
│      .eq('user_id', user_id)                                    │
│      .single()                                                  │
│      .execute()                                                 │
│                                                                  │
│  # Send to Expo API                                             │
│  requests.post('https://exp.host/--/api/v2/push/send', {       │
│      'to': 'ExponentPushToken[abc123...]',                      │
│      'title': '⚡ Life Update: Networking Drinks',              │
│      'body': 'You have been invited to networking drinks...'   │
│  })                                                              │
│                                                                  │
│  # Expo routes to your device                                   │
│  # Your device receives notification                            │
│  ✅ Notification appears in system tray!                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why You Lost Your Token When You Reinstalled

### What Happens During Reinstall:

1. **Uninstall**: App is removed from your device
   - Old token becomes invalid
   - Stored token on device deleted

2. **Reinstall**: You download the app again
   - App creates a **NEW token** on your device
   - Old token in database is now worthless

3. **Open App**: First time after reinstall
   - App calls `Notifications.getExpoPushTokenAsync()`
   - Gets the new token
   - Sends it to backend
   - Backend saves it ← **This is where our fix matters!**

### Before the Fix (Why You Didn't Get Notifications):
```
Backend received new token
    ↓
❌ Backend THREW IT AWAY (bug!)
    ↓
Later: "No token in database"
    ↓
Notifications failed
```

### After the Fix (Why Luma Got Notifications):
```
Backend received new token
    ↓
✅ Backend SAVED it to database (fixed!)
    ↓
Later: Token found in database
    ↓
Notifications work!
```

---

## How to Get Your Token Back (After Reinstalling)

### Automatic (Just Open the App):
```
1. Uninstall app
2. Reinstall app
3. Open app ← App automatically does this:
   - Calls Notifications.getExpoPushTokenAsync()
   - Sends token to /api/notification/register-token/
   - Backend saves it ✅
4. Close app (or leave it open)
5. Next time you get a life event → notification delivered!
```

**That's it!** The app handles it automatically.

### Debug (Check if Your Token is Saved):
```bash
# This shows which users have push tokens in the database
python my_flask_app/test_push_notification.py --list

# Your username should appear here if token was saved
```

---

## The Token Format (What It Looks Like)

```
ExponentPushToken[abc123xyz456def789ghi...]
```

**Parts:**
- `ExponentPushToken[` - Always starts with this
- `abc123xyz456...` - Unique device identifier (very long, random string)
- `]` - Always ends with this

**Valid examples:**
```
✅ ExponentPushToken[abc123xyz]
✅ ExponentPushToken[super_long_random_string_here_xyz789]
✅ ExponentPushToken[j1k2l3m4n5o6p7q8r9s0]
```

**Invalid examples (will be rejected):**
```
❌ abc123xyz (missing ExponentPushToken[ and ])
❌ ExponentPushToken[incomplete (missing closing ])
❌ MyCustomToken[xyz] (doesn't start with ExponentPushToken)
```

---

## Where the Token is Generated (Mobile App Code)

### Typical React Native / Expo Code (Pseudocode):

```javascript
// In your app's App.tsx or main component
import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';

async function registerForPushNotifications() {
  try {
    // 1. GET TOKEN from Expo infrastructure
    const token = (await Notifications.getExpoPushTokenAsync()).data;
    console.log('Push Token:', token);
    
    // 2. SAVE token locally (for reference)
    await AsyncStorage.setItem('pushToken', token);
    
    // 3. SEND token to backend
    const response = await fetch('https://api.example.com/api/notification/register-token/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${jwtToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        push_token: token  // Send token to backend
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('✅ Token registered with backend');
      // Backend now has your token and can send notifications!
    } else {
      console.log('❌ Failed to register token');
    }
  } catch (error) {
    console.error('Error registering for push notifications:', error);
  }
}

// Call this when app starts
useEffect(() => {
  registerForPushNotifications();
}, []);
```

### What `Notifications.getExpoPushTokenAsync()` Does:

```javascript
// Simplified version of what Expo does internally:

async function getExpoPushTokenAsync() {
  // 1. Check if device is registered with Expo infrastructure
  // 2. If not, register it
  // 3. Generate unique token for this device
  // 4. Return the token
  
  // This token is unique per device/app combination
  // Different devices = different tokens
  // Same device, app reinstalled = different token (new device registration)
  
  return {
    type: 'expo',
    data: 'ExponentPushToken[...]'  // The actual token
  };
}
```

---

## Where the Token is Stored (Database)

### Backend Database Schema:

```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE NOT NULL,
  username VARCHAR(255),
  
  -- Push notification fields (added by our fix!)
  expo_push_token VARCHAR(255),           -- The actual token
  push_token_updated_at TIMESTAMP,        -- When it was saved
  
  ... other fields ...
);
```

### After You Register Your Token:

```
Database Row for "Your User":
┌─────────────────────────────────────────────────────────┐
│ user_id: "8bffcbd1-065f-4f5f-a533-945934bb6ac7"        │
│ username: "Tester One"                                  │
│ expo_push_token: "ExponentPushToken[abc123xyz...]" ✅  │
│ push_token_updated_at: "2026-05-20T10:30:00Z" ✅       │
└─────────────────────────────────────────────────────────┘
```

### If No Token (Like You Now):

```
Database Row for "Your User":
┌─────────────────────────────────────────────────────────┐
│ user_id: "8bffcbd1-065f-4f5f-a533-945934bb6ac7"        │
│ username: "Tester One"                                  │
│ expo_push_token: NULL ❌                                │
│ push_token_updated_at: NULL ❌                          │
└─────────────────────────────────────────────────────────┘

Result: Backend can't send notifications (no address to send to!)
```

---

## The Backend Process (When Notification Needs to be Sent)

### Step 1: Retrieve Token
```python
def get_expo_token(user_id):
    # Query database for this user's token
    result = supabase.table('profiles') \
        .select('expo_push_token') \
        .eq('user_id', user_id) \
        .single() \
        .execute()
    
    if result.data and result.data.get('expo_push_token'):
        return result.data['expo_push_token']  # Found it!
    else:
        return None  # Not found (user reinstalled, or never registered)
```

### Step 2: Validate Token Format
```python
def validate_push_token(token):
    if not token:
        return False
    
    # Must be in format: ExponentPushToken[...]
    return (token.startswith('ExponentPushToken[') and 
            token.endswith(']'))
```

### Step 3: Send to Expo API
```python
def send_notification(token, title, body):
    payload = {
        'to': token,  # The token we retrieved
        'title': title,
        'body': body,
        'sound': 'default',
        'priority': 'high'
    }
    
    # Send HTTP POST to Expo
    response = requests.post(
        'https://exp.host/--/api/v2/push/send',
        json=payload
    )
    
    return response.json()  # Returns ticket confirmation
```

---

## What Happens If You Don't Register Your Token

**Scenario: You reinstall, but don't open the app**

```
Time T=0: You reinstall app (new device, new token exists)
  ↓
Time T=10min: Someone tries to send you a notification
  ↓
Backend queries database: "What's the token for this user?"
  ↓
Database returns: NULL (you never registered)
  ↓
Backend: "Can't send without a token"
  ↓
❌ Notification never sent
  ↓
Time T=30min: You open app (finally!)
  ↓
App: "Getting token..."
  ↓
App sends token to backend
  ↓
Backend: "Saving token now"
  ↓
Now when next notification tries to send → ✅ Works!
```

---

## Summary for Junior Devs

| Concept | Explanation |
|---------|-------------|
| **What is a token?** | A unique address for your device (like a mailbox ID) |
| **Who generates it?** | Expo infrastructure (when app calls `getExpoPushTokenAsync()`) |
| **When is it generated?** | When app starts and calls the Expo API |
| **Where is it stored?** | On your device (in app memory) AND in backend database |
| **When is it sent to backend?** | When app registers with `/api/notification/register-token/` |
| **What happens if you lose it?** | You get a new one when you reinstall and open the app |
| **Why does backend need it?** | To know which device to send the notification to |
| **Can the same token work for multiple devices?** | NO - each device gets a unique token |
| **Do tokens expire?** | Yes - old tokens become invalid over time or after reinstall |
| **What if backend doesn't have the token?** | Notification can't be sent (no delivery address) |

---

## How to Get Your Token Back Right Now

1. **Open your app** (if you have it reinstalled)
2. The app automatically:
   - Gets new token from Expo
   - Sends it to backend
   - Backend saves it ✅
3. **You're done!** Next notification will reach you

**To verify it worked:**
```bash
python my_flask_app/test_push_notification.py --list
# Your username should now appear with a token
```

---

## Key Takeaway

**Before Our Fix:**
- Token registration endpoint received the token
- ❌ Threw it away
- Backend had nothing to send with
- Notifications failed

**After Our Fix:**
- Token registration endpoint receives the token
- ✅ Saves it to database
- Backend retrieves it and sends notifications
- Notifications work!
**You just need to open your app once → everything else is automatic!**

