# Test Notification Logging

This document describes the notification logging system.

## How It Works

### 1. Sending a Notification
When you send a WebPush notification from the test page:
1. A `NotificationLog` entry is created with `status='pending'`
2. The log entry is saved to the database and gets an `id`
3. The `log_id` is passed in the notification metadata
4. The notification is sent via WebPush provider
5. The log status is updated to `sent` or `failed`

### 2. Click Tracking
When a user clicks a notification:
1. Service worker detects the click event
2. Extracts `log_id` from notification data
3. Sends message to any open browser tab/window
4. The page receives the message and calls `/api/v1/logs/<log_id>/click`
5. The backend marks the log entry as clicked

### 3. Viewing Logs
Visit the **Logs** page to see:
- All notifications sent to you
- Delivery status (sent/failed/pending)
- Whether each notification was clicked
- Click-through rate (CTR)
- Statistics by channel

## API Endpoints

- `GET /api/v1/logs` - List all logs (with filters)
- `GET /api/v1/logs/<id>` - Get specific log
- `POST /api/v1/logs/<id>/click` - Mark as clicked
- `GET /api/v1/logs/stats` - Get statistics

## Testing

1. **Send a notification**:
   - Go to Test WebPush page
   - Subscribe to notifications
   - Send a test notification
   - Note the log ID in the success message

2. **Check logs**:
   - Go to Logs page
   - You should see your notification listed
   - Status should be "sent"

3. **Test click tracking**:
   - Click on the notification in your browser
   - Return to Logs page
   - The notification should now show "Clicked: Yes"

## For ML Algorithms

The Sleeping Multi-Armed Bandit algorithm can use this data:
- `NotificationLog.clicked` - Boolean indicating user engagement
- `NotificationLog.template_id` - Which template was used
- `NotificationLog.channel` - Which channel performed best
- Click-through rates per template/channel

Query example:
```python
# Get CTR for a specific template
template_logs = NotificationLog.query.filter_by(
    template_id=123,
    status='sent'
).all()

total_sent = len(template_logs)
total_clicked = sum(1 for log in template_logs if log.clicked)
ctr = (total_clicked / total_sent * 100) if total_sent > 0 else 0
```
