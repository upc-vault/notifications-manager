# User Preferences & Behavior Tracking

## Overview
The notification system now includes comprehensive user behavior tracking and preference management to make ML algorithms more context-aware and user-friendly.

## Features Implemented

### 1. User Behavior Tracking
**Location:** `src/models/user.py`

New fields added to User model:
- `last_active_time` - Timestamp of last user activity
- `last_notification_clicked_at` - When user last clicked a notification
- `preferred_language` - User's preferred language (default: 'en')
- `timezone` - User's timezone (default: 'UTC')
- `device_type` - Primary device type (mobile, desktop, tablet)

New methods:
```python
user.update_last_active()  # Update last active timestamp
user.update_notification_clicked()  # Update last click timestamp
```

### 2. Engagement Metrics
**Location:** `src/models/notification_log.py`

New fields added to NotificationLog:
- `time_to_click` - Seconds from notification sent to clicked (auto-calculated)
- `device_type` - Device used to view/click notification
- `dismissed_at` - When notification was dismissed without clicking
- `read_duration` - How long notification was viewed (seconds)

Enhanced `mark_clicked()` method now:
- Automatically calculates `time_to_click`
- Updates user's `last_notification_clicked_at`
- Essential for ML training on user responsiveness

### 3. User Preferences Model
**Location:** `src/models/user_preferences.py`

New comprehensive preferences model with:

**Quiet Hours (Do Not Disturb):**
- `quiet_hours_enabled` - Enable/disable quiet hours
- `quiet_hours_start` - Start time (e.g., 22:00)
- `quiet_hours_end` - End time (e.g., 08:00)
- Handles overnight periods correctly

**Rate Limiting:**
- `max_notifications_per_day` - Daily limit (default: 50)
- `max_notifications_per_hour` - Hourly limit (default: 10)
- Emergency notifications bypass limits

**Channel Preferences:**
- `preferred_channels` - JSON array of channel priority order
- `email_enabled`, `sms_enabled`, `push_enabled`, `whatsapp_enabled`
- Individual channel opt-in/opt-out

**Content Preferences:**
- `marketing_opt_in` - Accept marketing communications
- `promotional_opt_in` - Accept promotional offers
- `prefer_short_messages` - Prefer concise messages
- `prefer_rich_content` - Enable images, buttons, etc.

**Accessibility:**
- `high_contrast_mode` - High contrast notifications
- `large_text_mode` - Larger text size

**Key Methods:**
```python
prefs.is_in_quiet_hours()  # Check if currently in quiet hours
prefs.can_send_notification('promotional')  # Check rate limits
prefs.is_channel_enabled('sms')  # Check if channel is enabled
prefs.get_preferred_channels()  # Get list of enabled channels
```

### 4. Intelligent Channel Selection
**Location:** `src/services/notification_decision_service.py`

New method: `_get_disabled_channels(user_preferences, message_type, notification_type)`

**Time-Based Channel Selection:**
- **Night (22:00-06:00)**: Only silent channels (email, web)
  - Disables: SMS, Push, WhatsApp
  - Exception: Urgent/Security notifications allowed
  
- **Evening (18:00-22:00)**: Limited promotional reach
  - Promotional notifications: Only email/web
  - Informational/Urgent: All enabled channels

**Preference-Based Filtering:**
- Respects user channel opt-ins
- During quiet hours: Uses only silent channels
- Always allows urgent/security through any enabled channel

**Marketing Opt-Out:**
- If `promotional_opt_in = False`, promotional/marketing templates are excluded
- Respects user's content preferences

### 5. Enhanced ML Decision Reasoning
**Location:** `src/services/notification_decision_service.py`

Updated `_generate_reasoning()` to include:
- Sleeping Bandit template selection explanation
- Tug of War channel selection details
- List of disabled channels and why
- Quiet hours status
- Time-based restrictions

Example output:
```
User PREMIUM | young tech-savvy | high digital adoption (90%) | 
Template 'Account Security Alert' selected by Sleeping Bandit (affinity 0.85) | 
Channel 'email' selected by Tug of War (affinity 0.78) | 
Excluded: sms, push, whatsapp | Quiet hours active - silent channels preferred | 
Priority HIGH
```

### 6. API Endpoints
**Location:** `src/api/preferences.py`

New endpoints:
- `GET /api/v1/preferences/` - Get user preferences
- `PUT /api/v1/preferences/` - Update preferences
- `POST /api/v1/preferences/quiet-hours` - Set quiet hours
- `GET /api/v1/preferences/channels` - Get channel preferences
- `PUT /api/v1/preferences/channels` - Update channel preferences

All endpoints require authentication (JWT token).

### 7. Preferences UI
**Location:** `templates/preferences.html`

User-friendly web interface with:
- Quiet hours toggle and time pickers
- Rate limiting controls
- Channel enable/disable switches
- Content preference toggles
- Marketing opt-in/opt-out
- Accessibility options
- Real-time save with success/error feedback

Accessible at: `/preferences` (requires login)

## Usage

### 1. Run Database Migration
```powershell
python scripts/migrate_database.py
```

This will:
- Add new columns to `user` table
- Add new columns to `notification_log` table
- Create `user_preferences` table

### 2. Start the Application
```powershell
python src/api/main.py
```

### 3. Set User Preferences
1. Login to the application
2. Navigate to **Preferences** in the menu
3. Configure your notification preferences
4. Click **Save Preferences**

### 4. Test the System

**Test Quiet Hours:**
```python
# Set quiet hours (22:00 - 08:00)
# Send notification during quiet hours
# Result: Only email/web channels used
```

**Test Channel Preferences:**
```python
# Disable SMS in preferences
# Send notification
# Result: SMS not used, other channels selected
```

**Test Time-Based Selection:**
```python
# Send promotional notification at night (23:00)
# Result: Only silent channels (email, web) used
```

**Test Marketing Opt-Out:**
```python
# Disable promotional_opt_in
# Send promotional notification
# Result: Promotional templates excluded
```

## How It Works

### Decision Flow
1. **Load User Preferences:** Decision service loads UserPreferences from database
2. **Check Rate Limits:** Verify user hasn't exceeded daily/hourly limits
3. **Time-Based Logic:** Determine current time period (night, evening, day)
4. **Disable Channels:** Build list of disabled channels based on:
   - User channel opt-ins
   - Quiet hours status
   - Current time period
   - Message urgency
5. **Template Selection:** Sleeping Bandit chooses template (excludes promotional if opted out)
6. **Channel Selection:** Tug of War picks from enabled channels only
7. **Generate Decision:** Create decision with enhanced reasoning

### ML Algorithm Integration

**Sleeping Bandit (Template Selection):**
- Now respects `promotional_opt_in` preference
- Excludes promotional/marketing templates if user opted out
- Still learns from user engagement (time_to_click)

**Tug of War (Channel Selection):**
- Receives `disabled_channels` parameter
- Filters channels before probability calculation
- Considers only enabled channels for selection
- Emergency fallback if all channels disabled

### Engagement Tracking
```python
# When notification is clicked
log = NotificationLog.query.get(log_id)
log.mark_clicked()  # Automatically calculates time_to_click
# Updates user.last_notification_clicked_at
```

## Configuration Examples

### Example 1: Night Worker
```json
{
  "quiet_hours_enabled": true,
  "quiet_hours_start": "08:00",
  "quiet_hours_end": "16:00",
  "preferred_channels": ["email", "push", "sms"],
  "sms_enabled": true,
  "push_enabled": true
}
```

### Example 2: Minimal Notifications
```json
{
  "max_notifications_per_day": 10,
  "max_notifications_per_hour": 2,
  "marketing_opt_in": false,
  "promotional_opt_in": false,
  "email_enabled": true,
  "sms_enabled": false,
  "push_enabled": false
}
```

### Example 3: WhatsApp Only
```json
{
  "preferred_channels": ["whatsapp"],
  "email_enabled": false,
  "sms_enabled": false,
  "push_enabled": false,
  "whatsapp_enabled": true
}
```

## Benefits

1. **Better User Experience:**
   - Respect user's time with quiet hours
   - Honor channel preferences
   - Prevent notification fatigue with rate limits

2. **Improved ML Performance:**
   - More engaged users = better click rates
   - Time-to-click metrics help identify effective patterns
   - Context-aware decisions improve relevance

3. **Privacy & Control:**
   - Users control what they receive and how
   - Marketing opt-out respected
   - Accessibility options for all users

4. **Smart Defaults:**
   - System still works without preferences set
   - Intelligent time-based fallbacks
   - Emergency notifications always delivered

## Database Schema

### user_preferences table
```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    quiet_hours_enabled BOOLEAN DEFAULT 0,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    max_notifications_per_day INTEGER DEFAULT 50,
    max_notifications_per_hour INTEGER DEFAULT 10,
    preferred_channels TEXT,  -- JSON array
    email_enabled BOOLEAN DEFAULT 1,
    sms_enabled BOOLEAN DEFAULT 1,
    push_enabled BOOLEAN DEFAULT 1,
    whatsapp_enabled BOOLEAN DEFAULT 1,
    marketing_opt_in BOOLEAN DEFAULT 1,
    promotional_opt_in BOOLEAN DEFAULT 1,
    prefer_short_messages BOOLEAN DEFAULT 0,
    prefer_rich_content BOOLEAN DEFAULT 1,
    high_contrast_mode BOOLEAN DEFAULT 0,
    large_text_mode BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

## Troubleshooting

**Issue:** Preferences not saving
- Check JWT token is valid
- Verify user is authenticated
- Check browser console for errors

**Issue:** Notifications still sent during quiet hours
- Verify `quiet_hours_enabled = True`
- Check time format is correct (HH:MM)
- Ensure preferences were saved successfully

**Issue:** All channels disabled
- System falls back to all enabled channels for urgent notifications
- Check at least one channel is enabled in preferences
- Review channel opt-in settings

## Future Enhancements

Potential additions:
- Per-template preferences (disable specific templates)
- Smart quiet hours (learn from user behavior)
- Notification scheduling (delay until preferred time)
- Do Not Disturb for specific time periods
- Channel priority reordering by drag-and-drop
- A/B testing for template effectiveness

## API Reference

See [preferences.py](src/api/preferences.py) for detailed API documentation.
