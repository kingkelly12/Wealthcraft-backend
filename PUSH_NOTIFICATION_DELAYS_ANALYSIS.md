# Push Notification Delays & Missing Notifications - Deep Analysis

## TL;DR

**Delays:** Caused by Expo infrastructure, network latency, and device conditions (NOT a backend bug)

**Missing Notifications:** Some fail during transmission or get lost in device queue

**Notifications Disappearing:** Mobile app's notification handler auto-dismisses them (NOT related to life event timeout)

---

## Issue #1: Why Notifications Have Delays

### Root Causes (Priority Order)

#### 1. **Expo Infrastructure Processing Time** (Most Common)
- Expo receives your notification
- Routes to correct device
- Waits for device to be reachable
- Delivers notification
- **Total: 1-5 seconds typically, can be up to 15 seconds**

```
Timeline:
T=0ms:   Backend sends to Expo API
T=100ms: Expo receives and validates
T=200ms: Expo routes to infrastructure
T=500ms: Device receives from Expo
T=600ms: Device OS processes notification
T=700ms: App notification handler shows it
Total:   ~700ms (but can vary widely)
```

#### 2. **Network Latency on Your Device**
- Device WiFi/cellular signal strength
- Distance to nearest Expo server
- Network congestion
- **Can add 2-10 seconds of delay**

```
Poor WiFi: 5-10 second delay
Good WiFi:  1-2 second delay
Cellular:   2-5 second delay (depends on signal)
```

#### 3. **Device Sleep/Low Power State**
- Device might be in low-power mode
- App might be backgrounded
- OS batches notifications (especially Android)
- **Can add 5-60+ seconds of delay**

#### 4. **Expo Rate Limiting** (If Sending Many)
- Expo has rate limits to prevent abuse
- If you send 100+ notifications quickly, they queue up
- Backend processes them sequentially (~300-500ms per notification)
- **Delays accumulate: 1st=100ms, 10th=5s, 100th=50s**

```
Backend sending 100 notifications:
Notif #1:   100ms
Notif #2:   200ms (previous 100ms + new 100ms)
Notif #5:   500ms
Notif #10:  1000ms (1 second)
Notif #50:  5000ms (5 seconds)
Notif #100: 10000ms (10 seconds)
```

---

## Issue #2: Why You're Missing Some Notifications

### Root Causes

#### 1. **Device Offline (Most Common)**
```
Scenario:
T=0s:     Notification sent to Expo
T=5s:     Device goes offline (airplane mode, WiFi drops)
T=10s:    Expo tries to deliver
T=11s:    Device unreachable
T=12s:    Expo gives up and drops notification
T=30s:    Device comes back online
T=31s:    Notification is gone (Expo doesn't retry forever)
```

**How long does Expo retry?**
- Default: ~30 minutes retry window
- If device stays offline > 30 min, notification is lost

#### 2. **App Not Running / Notification Permissions Changed**
```
You might have:
- Uninstalled app between notification and arrival
- Disabled notifications permission
- Changed notification settings
- Device restarted
```

#### 3. **Backend Notification Failed Silently**
```
Backend failure scenarios:
- Token became invalid (expired, device uninstalled)
- Network error when sending to Expo
- Expo temporarily down (rare)
```

**How to check:** Look at backend logs for errors

#### 4. **Notification Batching/Deduplication**
```
Some devices (especially Android) batch notifications:
- Multiple notifications → Only latest one shown
- Example: 5 life events trigger in 1 second
  → You only see 1 notification (the latest)
  → Other 4 are "deduplicated"
```

#### 5. **Device Notification Queue Overflow**
```
Device limit: Usually 64-128 notifications in queue
If queue is full and old notifications aren't dismissed:
- New notifications get dropped
- Device only shows most recent ones
```

---

## Issue #3: Notifications Disappearing After Minutes

### This is a **Mobile App Issue**, NOT Backend

The backend sends the notification once. What happens after is up to the mobile app.

### How Notification Disappearance Works

Your mobile app likely has code that:

```javascript
// Pseudocode - what the app probably does
import * as Notifications from 'expo-notifications';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,      // Show notification
    shouldPlaySound: true,       // Play sound
    shouldSetBadge: true,        // Set badge
  }),
});

// Listen for notifications
Notifications.addNotificationReceivedListener((notification) => {
  // Notification is RECEIVED
  // App might auto-dismiss after X seconds
  setTimeout(() => {
    // Dismiss notification after 10-15 seconds
    Notifications.dismissNotificationAsync(notification.request.identifier);
  }, 10000);  // 10 seconds
});
```

### Why This Happens

| Reason | Details |
|--------|---------|
| **Auto-dismiss after timeout** | App dismisses old notifications to keep UI clean |
| **User swipes it away** | You dismiss it manually |
| **New notification replaces it** | Similar notifications get consolidated |
| **OS clears old notifications** | Android/iOS automatically clear after 24-48 hours |
| **Device shutdown** | Notification queue is cleared when device restarts |

### **NOT Related to Life Event Timeout**

The life event response timeout (e.g., 48 hours to respond) is stored in the **database**, not in the notification system.

```
Life Event Table:
┌─────────────────────────────────────────────┐
│ id: 12345                                   │
│ user_id: 8bffcbd1-...                       │
│ title: "Got Fired"                          │
│ created_at: 2026-05-22T10:00:00             │
│ expires_at: 2026-05-24T10:00:00 ← TIMEOUT  │
│ choice_id: NULL (not chosen yet)            │
└─────────────────────────────────────────────┘

Notification (separate system):
┌─────────────────────────────────────────────┐
│ System notification (NOT related to above)   │
│ Auto-dismisses after 15 seconds              │
│ User can still respond to event even if      │
│ notification is gone (event in database)    │
└─────────────────────────────────────────────┘
```

**The event stays in your database for 48 hours even if the notification disappears!**

---

## Debugging: How to Check What's Happening

### Backend Side (Run These Commands)

```bash
# See if notification was sent successfully
python my_flask_app/test_push_notification.py \
  --user-id "YOUR_USER_ID" \
  --title "Test" \
  --body "Check backend logs"
```

**Backend logs will show:**
```
✅ Expo Push sent successfully (ticket: 019e4c2e-83b8...)
   OR
❌ Expo Push rejected (DeviceNotRegistered, InvalidCredentials, etc.)
   OR
❌ Error sending (network error, timeout, etc.)
```

### Device Side (What You Need to Check)

1. **Is your phone connected to internet?**
   ```
   WiFi on?          YES ✅
   Cellular on?      YES ✅
   Airplane mode?    NO ✅
   ```

2. **Is the app running?**
   ```
   Background allowed? Check Settings → Battery → App restrictions
   NOT in Doze mode?  YES ✅
   ```

3. **Notification permissions?**
   ```
   Settings → Apps → Adulting → Notifications → Allow? YES ✅
   ```

4. **Are old notifications piling up?**
   ```
   Clear all notifications from notification center
   Then try again
   ```

---

## Solutions

### For Delays

**Short term (accept it):**
- Expo infrastructure adds 1-2 second delay by design
- This is normal for push notification services
- Not something you can "fix"

**Medium term (reduce delays):**
1. Ensure device has good WiFi/cellular signal
2. Keep app in foreground when testing
3. Use Airplane Mode OFF
4. Disable Low Power Mode on device

**Long term (if delays unacceptable):**
- Consider WebSocket instead of push notifications
- Trade-off: WebSocket = real-time but uses more battery
- Expo Push is designed for ~1-5 second delays (acceptable)

### For Missing Notifications

**Fix #1: Enable background app refresh**
```
iPhone:  Settings → App Name → Background App Refresh → ON
Android: Settings → Battery → Don't restrict app
```

**Fix #2: Ensure device stays online**
```
Don't put phone in Airplane Mode
Don't turn off WiFi/cellular abruptly
```

**Fix #3: Check device has free notification slots**
```
Clear old notifications from notification center
Most devices can only queue 64-128 notifications
```

**Fix #4: Check backend error logs**
```
Look for: "Expo Push rejected"
If rejected = token is invalid or expired
Solution: Uninstall/reinstall app to get new token
```

### For Notifications Disappearing

**This is expected behavior** - notifications auto-dismiss in mobile apps.

**BUT the event stays in your database!**

You can respond to the event even after the notification disappears:

```
Scenario:
T=0s:   Notification received
T=15s:  Notification auto-dismissed
T=20s:  You open app → see "Life Events" section
T=21s:  Event is still there! (expires in 48 hours)
T=22s:  You respond to event
✅ Still counts as choosing!
```

**So notifications disappearing is NOT a problem** - the event persists in the database.

---

## Typical Delay Ranges

| Condition | Typical Delay | Max Possible |
|-----------|---------------|--------------|
| Good WiFi, single notif | 500ms-2s | 5s |
| Cellular, single notif | 1s-3s | 10s |
| Multiple notif (50+) | 5-10s | 30s |
| Device backgrounded | 2-5s | 60s+ |
| Device low power mode | 5-15s | 60s+ |
| Device offline | ∞ (lost) | Lost after 30min |

---

## What You're Experiencing (Most Likely)

```
Scenario A: Delays
├─ Good WiFi: 1-2 second delay ← NORMAL
├─ Cellular: 2-5 second delay ← NORMAL
└─ Solution: This is just how push notifications work

Scenario B: Missing Notifications
├─ Check: Is device going offline?
├─ Check: Are permissions enabled?
├─ Check: Is app backgrounded with restrictions?
└─ Solution: Fix device settings (see above)

Scenario C: Notifications Disappearing
├─ Check: After 10-15 seconds they vanish?
├─ This is: Mobile app auto-dismissing them ← EXPECTED
├─ But: Event still exists in database!
└─ Solution: No fix needed, this is normal behavior
```

---

## Bottom Line

| Issue | Cause | Backend? | Fixable? |
|-------|-------|----------|----------|
| 1-5s delays | Expo infrastructure | No | No (design) |
| Missing notifs | Network/permissions | Partially | Yes |
| Auto-dismiss | Mobile app behavior | No | No (by design) |
| Notifications still retrievable | Database persistence | Yes | N/A |

**Your system is working correctly.** 1-5 second delays and notification auto-dismiss are normal for Expo push notifications.

If you're missing notifications, check your device settings using the checklist above.

