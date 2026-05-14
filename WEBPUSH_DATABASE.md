# WebPush Subscription Database Integration

## Overview
WebPush subscriptions are now persisted in SQLite database, replacing the previous in-memory storage.

## Database Schema

### Table: `webpush_subscriptions`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `user_id` | Integer | Foreign key to users table |
| `endpoint` | String(500) | Push endpoint URL (unique) |
| `p256dh_key` | String(200) | Public encryption key |
| `auth_key` | String(100) | Authentication secret |
| `user_agent` | String(500) | Browser user agent |
| `is_active` | Boolean | Subscription status (default: True) |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `last_used_at` | DateTime | Last successful notification |
| `notifications_sent` | Integer | Success counter |
| `notifications_failed` | Integer | Failure counter |

### Relationships
- One user can have one active webpush subscription
- Subscription links to `users` table via `user_id`

## Key Changes

### 1. Database Model
**File**: `src/models/webpush_subscription.py`
- Created `WebPushSubscription` SQLAlchemy model
- Tracks statistics (sent, failed, last_used)
- Automatic deactivation on 410 Gone errors
- Methods: `to_subscription_dict()`, `increment_sent()`, `increment_failed()`, `deactivate()`

### 2. Subscription Manager
**File**: `src/providers/webpush_provider.py`
- Replaced in-memory dictionary with database queries
- `add_subscription()` - Creates or updates subscription in DB
- `get_subscription()` - Queries by user_id
- `get_subscription_by_username()` - Queries by username (for API)
- `remove_subscription()` - Deactivates subscription
- `mark_success()` / `mark_failed()` - Updates statistics
- Auto-deactivates on HTTP 410 (subscription expired)

### 3. API Endpoints (JWT Protected)

#### Subscribe to Push
```
POST /api/v1/webpush/subscribe
Headers: Authorization: Bearer <JWT_TOKEN>
Body: { "subscription": { "endpoint": "...", "keys": {...} } }
```
- Automatically gets username from JWT token
- Captures browser user agent
- Updates existing subscription if endpoint already exists

#### Unsubscribe
```
POST /api/v1/webpush/unsubscribe
Headers: Authorization: Bearer <JWT_TOKEN>
```
- Uses JWT username automatically
- No request body needed

#### Send Test Notification
```
POST /api/v1/webpush/test
Headers: Authorization: Bearer <JWT_TOKEN>
Body: { "title": "...", "body": "...", "icon": "...", "url": "..." }
```
- Sends to current user's subscription
- All fields optional (has defaults)

#### Get All Subscriptions
```
GET /api/v1/webpush/subscriptions
Headers: Authorization: Bearer <JWT_TOKEN>
```
- Returns all active subscriptions with statistics

### 4. Frontend Updates
**File**: `templates/test_webpush.html`
- User ID field now auto-filled from JWT (read-only)
- Removed `user_id` from API requests (uses JWT automatically)
- All requests go through `auth.apiRequest()` for automatic token handling

## Benefits

1. **Persistence**: Subscriptions survive server restarts
2. **Statistics**: Track success/failure rates per subscription
3. **User Agent Tracking**: Know which browsers are subscribed
4. **Automatic Cleanup**: 410 Gone errors deactivate subscriptions
5. **Audit Trail**: Created/updated/last_used timestamps
6. **Security**: JWT authentication required for all operations
7. **Multi-device**: Can extend to support multiple subscriptions per user

## Statistics Tracking

Each subscription tracks:
- `notifications_sent` - Incremented on successful delivery
- `notifications_failed` - Incremented on errors
- `last_used_at` - Updated on each successful send
- `is_active` - Set to False on 410 Gone (expired subscription)

## Error Handling

### HTTP 410 Gone
When a browser endpoint returns 410 (subscription expired):
1. Subscription marked as `is_active = False`
2. `notifications_failed` counter incremented
3. Future attempts skip inactive subscriptions

### Other Errors
- All errors increment `notifications_failed`
- Subscription remains active for retry
- Error details logged in DeliveryResult

## Migration Notes

**No data migration needed** - Old in-memory subscriptions are lost on restart (expected behavior).

Users will need to:
1. Visit `/test/webpush`
2. Click "Subscribe to Push Notifications"
3. Grant browser permission
4. Subscription saved to database automatically

## Database Creation

Database table created automatically on app startup via:
```python
with app.app_context():
    db.create_all()
```

Located at: `data/notifications.db`

## Security

- All WebPush endpoints require JWT authentication (`@jwt_required()`)
- User can only subscribe/unsubscribe their own account
- Endpoint URLs stored but encrypted keys (p256dh, auth) maintained
- VAPID authentication for push protocol security

## Future Enhancements

1. **Multiple Subscriptions**: Support multiple devices per user
2. **Subscription Groups**: Group notifications by topic/channel
3. **TTL Management**: Automatic cleanup of old inactive subscriptions
4. **Analytics Dashboard**: Visualize subscription statistics
5. **Push Preferences**: Per-user notification settings
