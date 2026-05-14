# WhatsApp Business API Setup Guide

## Overview

The notification manager now supports **real WhatsApp Business API integration** using Meta's Cloud API. By default, it runs in **mock mode** for testing without credentials.

## Pricing

- **First 1,000 conversations/month: FREE**
- After that: $0.005 - $0.15 per conversation (varies by country)
- Conversation = 24-hour message window with a user
- [Official Pricing](https://developers.facebook.com/docs/whatsapp/pricing)

## Prerequisites

1. **Meta Business Account** (free)
2. **Facebook Developer Account** (free)
3. **WhatsApp Business Account** (free)
4. **Phone number** dedicated to API use (cannot use regular WhatsApp)
5. **Business verification** by Meta

## Setup Steps

### 1. Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/apps)
2. Click **"Create App"**
3. Select **"Business"** type
4. Fill in app details and create

### 2. Add WhatsApp Product

1. In your app dashboard, click **"Add Product"**
2. Find **"WhatsApp"** and click **"Set Up"**
3. Go to **"API Setup"** in the left menu

### 3. Get Credentials

You'll need two values:

#### Phone Number ID
- In **API Setup**, you'll see a **"From" phone number**
- Click on it to see the **Phone Number ID** (starts with numbers)
- Copy this value

#### Access Token
- In **API Setup**, you'll see a **"Temporary access token"**
- Copy this token (valid for 24 hours for testing)
- For production, create a **System User** token (never expires)

### 4. Configure System User Token (Production)

For permanent access:

1. Go to **Business Settings** → **Users** → **System Users**
2. Create a new system user
3. Add WhatsApp permissions
4. Generate token with `whatsapp_business_messaging` and `whatsapp_business_management` permissions
5. Copy the token (store securely!)

### 5. Configure Environment

Create a `.env` file in the project root or set environment variables:

```bash
# WhatsApp Business API Configuration
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_ACCESS_TOKEN=your_access_token_here
WHATSAPP_API_VERSION=v18.0
WHATSAPP_MOCK_MODE=false
```

Or in PowerShell:
```powershell
$env:WHATSAPP_PHONE_NUMBER_ID="your_phone_number_id_here"
$env:WHATSAPP_ACCESS_TOKEN="your_access_token_here"
$env:WHATSAPP_MOCK_MODE="false"
```

### 6. Test Configuration

1. Restart the Flask server
2. Go to `/test/whatsapp`
3. Enter a WhatsApp number (must be registered with WhatsApp)
4. Send a test message
5. Check the console for success/error messages

## Message Types

### Text Message
Simple text message (requires 24-hour conversation window or template)

```json
{
  "phone_number": "+1234567890",
  "message": "Hello from BBVA!",
  "type": "text"
}
```

### Template Message
Pre-approved message template (can be sent anytime)

```json
{
  "phone_number": "+1234567890",
  "type": "template",
  "template_name": "account_alert",
  "template_parameters": ["John", "$100.00"]
}
```

### Interactive Message
Message with buttons

```json
{
  "phone_number": "+1234567890",
  "message": "Your account has been updated",
  "type": "interactive",
  "buttons": [
    {
      "type": "reply",
      "reply": {
        "id": "view_account",
        "title": "View Account"
      }
    }
  ]
}
```

## Creating Message Templates

Templates must be created and approved in Meta Business Manager:

1. Go to **WhatsApp Manager** → **Message Templates**
2. Click **"Create Template"**
3. Choose category (Marketing, Utility, or Authentication)
4. Add template content with placeholders: `{{1}}`, `{{2}}`, etc.
5. Submit for approval (usually takes a few hours)
6. Once approved, use the template name in API calls

### Template Example

**Name:** `account_alert`  
**Category:** Utility  
**Content:**
```
Hello {{1}},

Your BBVA account has been updated. New balance: {{2}}.

If you didn't authorize this, contact us immediately.
```

**Usage:**
```python
whatsapp_provider.send_template_message(
    phone_number="+1234567890",
    template_name="account_alert",
    parameters=["John Doe", "$1,250.00"]
)
```

## Testing

### Test Phone Numbers

During development, you can add test phone numbers:

1. Go to **API Setup** → **Add phone numbers**
2. Enter your personal WhatsApp number
3. Verify with the code sent
4. Test without affecting real users

### Mock Mode

If credentials are not configured, the system automatically uses mock mode:
- Simulates API calls with realistic latency
- 92% success rate
- No real messages sent
- Perfect for development and testing

## Production Checklist

- [ ] Business verification approved by Meta
- [ ] System User token generated
- [ ] Tokens stored securely (environment variables, secret manager)
- [ ] Message templates created and approved
- [ ] Webhook configured for delivery status (optional)
- [ ] Rate limiting configured
- [ ] Error handling tested
- [ ] Logging configured
- [ ] Monitoring set up

## Troubleshooting

### "No active phone number found"
- Verify your phone number is activated in Meta Business Manager
- Check that WHATSAPP_PHONE_NUMBER_ID is correct

### "Invalid access token"
- Token may have expired (temporary tokens last 24 hours)
- Generate a System User token for permanent access
- Check token has correct permissions

### "Message not sent"
- Recipient number must be registered with WhatsApp
- For business-initiated messages, use approved templates
- Check if conversation window is open (24 hours from user's last message)

### "Template not found"
- Template must be created in Meta Business Manager
- Template must be approved before use
- Template name must match exactly (case-sensitive)

## Rate Limits

- **80 messages per second** per phone number
- **1000 messages per day** for unverified businesses
- **Unlimited** for verified businesses (subject to quality rating)

## Quality Rating

Meta assigns a quality rating based on:
- User block rate
- User report rate
- Message delivery rate

**Maintain high quality to avoid rate limiting!**

## Resources

- [WhatsApp Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Message Templates Guide](https://developers.facebook.com/docs/whatsapp/message-templates)
- [Pricing Information](https://developers.facebook.com/docs/whatsapp/pricing)
- [Best Practices](https://developers.facebook.com/docs/whatsapp/guides/best-practices)

## Support

For issues with Meta's platform:
- [Meta Business Help Center](https://www.facebook.com/business/help)
- [Developer Community](https://developers.facebook.com/community/)
