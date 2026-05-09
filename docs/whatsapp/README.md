# WhatsApp Business API Integration

## Overview

This implementation supports WhatsApp Business API messaging through multiple providers:
- **Twilio** - Easiest setup with sandbox for free testing
- **360dialog** - Template-focused with official WhatsApp partnership
- **MessageBird** - Omnichannel platform with WhatsApp integration

## Quick Start (Demo Mode)

The service works in **demo mode** without any credentials configured:

```bash
# No environment variables needed
# Messages will be logged to console instead of being sent
```

This is perfect for testing the API and UI without incurring costs.

## Provider Setup

### Option 1: Twilio (Recommended for Testing)

**Pros:**
- Free sandbox for testing (no business verification needed)
- Easiest setup
- Pay-as-you-go pricing
- Great documentation

**Cons:**
- Sandbox requires users to opt-in with a code
- Production requires business verification

**Setup Steps:**

1. **Sign up**: https://www.twilio.com/whatsapp
2. **Get Credentials**:
   - Go to Twilio Console
   - Find your **Account SID** and **Auth Token**
3. **Get WhatsApp Number**:
   - For testing: Use Twilio Sandbox number (+14155238886)
   - For production: Request your own number
4. **Configure Environment Variables**:

```bash
# .env file
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=+14155238886
```

5. **Test with Sandbox**:
   - Send "join <your-sandbox-keyword>" to +14155238886 from your phone
   - Now you can send messages to your phone number

**Pricing**: $0.005 - $0.068 per message depending on country

### Option 2: 360dialog

**Pros:**
- Official WhatsApp Business Solution Provider
- Template-focused approach
- European data hosting options
- Good for enterprise

**Cons:**
- More expensive (€25-€50/month minimum)
- Requires business verification upfront
- Setup takes longer

**Setup Steps:**

1. **Sign up**: https://www.360dialog.com/
2. **Register WhatsApp Business Account**:
   - Provide business documents
   - Wait for Meta approval (2-5 days)
3. **Get API Key**:
   - Log in to 360dialog Hub
   - Create API key
4. **Create Templates**:
   - Design message templates
   - Submit for WhatsApp approval
   - Wait 24-48 hours for approval
5. **Configure Environment Variables**:

```bash
# .env file
WHATSAPP_PROVIDER=360dialog
DIALOG360_API_KEY=your_api_key_here
DIALOG360_NAMESPACE=your_namespace_id
```

**Pricing**: Per conversation model, typically €25-50/month minimum

### Option 3: MessageBird

**Pros:**
- Multi-channel (SMS, WhatsApp, Voice, etc.)
- Good API documentation
- Conversations API for unified messaging

**Cons:**
- $25-50/month minimum
- Requires business verification
- More complex setup for multi-channel

**Setup Steps:**

1. **Sign up**: https://www.messagebird.com/whatsapp
2. **Business Verification**:
   - Submit business documents
   - Wait for Meta approval
3. **Create WhatsApp Channel**:
   - Go to Channels in Dashboard
   - Add WhatsApp Business
   - Get Channel ID
4. **Get API Key**:
   - Dashboard → Developers → API Keys
5. **Configure Environment Variables**:

```bash
# .env file
WHATSAPP_PROVIDER=messagebird
MESSAGEBIRD_API_KEY=your_api_key_here
MESSAGEBIRD_CHANNEL_ID=your_channel_id_here
```

**Pricing**: $0.01 - $0.05 per message + $25-50/month minimum

## API Usage

### Send Simple Message

```bash
curl -X POST http://localhost:8080/api/v1/whatsapp/send-test \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Hello from Omega Notifications!"
  }'
```

### Send Template Message (360dialog)

```bash
curl -X POST http://localhost:8080/api/v1/whatsapp/send-template \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "template_name": "hello_world",
    "template_params": ["John"]
  }'
```

### Check Service Status

```bash
curl http://localhost:8080/api/v1/whatsapp/status
```

## Phone Number Format

**Important**: Always use E.164 format with country code:

✅ Correct:
- +1234567890 (US)
- +34612345678 (Spain)
- +447911123456 (UK)

❌ Incorrect:
- 1234567890 (missing +)
- 612345678 (missing country code)
- +34 612 345 678 (spaces not allowed by some providers)

## Business Verification Requirements

To use WhatsApp Business API in production, you need:

1. **Business Documentation**:
   - Business name and address
   - Business registration documents
   - Tax ID or equivalent
   - Website (recommended)

2. **Facebook Business Manager Account**:
   - Create at business.facebook.com
   - Verify your business
   - Add WhatsApp Business Account

3. **Phone Number**:
   - Dedicated phone number (cannot be used with regular WhatsApp)
   - Can be landline or mobile
   - Must be able to receive verification code

4. **Approval Time**: 2-5 business days typically

## Message Templates

For business-initiated conversations (outside 24-hour window), you need approved templates:

### Template Components:
- **Header** (optional): Text, media, or document
- **Body**: Main message text with variables
- **Footer** (optional): Small print
- **Buttons** (optional): Quick replies or CTAs

### Example Template:
```
Name: order_confirmation
Category: TRANSACTIONAL

Header: Your order is confirmed! 🎉
Body: Hi {{1}}, your order #{{2}} will arrive on {{3}}.
Footer: Thank you for shopping with us
Button: Track Order (URL)
```

### Template Variables:
- Use {{1}}, {{2}}, etc. for dynamic content
- Must specify category (MARKETING, TRANSACTIONAL, UTILITY)
- Marketing templates have stricter approval

## Cost Analysis

### Message Costs by Country (Approximate)

| Region | Business-Initiated | User-Initiated Response |
|--------|-------------------|------------------------|
| North America | $0.033 | Free |
| Western Europe | $0.068 | Free |
| Latin America | $0.028 | Free |
| Asia Pacific | $0.040 | Free |
| Middle East | $0.042 | Free |

### 24-Hour Window Rule:
- When user messages you: 24-hour window opens
- During window: Send any message for free
- After window: Must use template (charged)

### Monthly Minimums:
- Twilio: $0 (pay-as-you-go)
- 360dialog: €25-50
- MessageBird: $25-50

### Budget Optimization:
1. **Use free channels first**: WebPush, Email
2. **Template messages**: Lower cost than freeform
3. **Respond to users**: Leverage 24-hour free window
4. **Batch messages**: Multiple messages in one conversation
5. **Test in sandbox**: Twilio sandbox is completely free

## Free Alternatives

If WhatsApp costs are prohibitive:

1. **WebPush** (FREE)
   - Browser notifications
   - Works on all devices
   - Instant delivery
   - Already implemented in this system

2. **Email** (FREE tier)
   - SendGrid: 100 emails/day free
   - AWS SES: $0.10 per 1000 emails
   - Mailgun: 5,000 emails/month free

3. **Push Notifications** (FREE for Android)
   - Firebase Cloud Messaging
   - iOS requires $99/year Apple Developer Program
   - Already implemented with iOS and Android apps

## Testing Checklist

- [ ] Demo mode works (no credentials)
- [ ] Phone number formatting validated
- [ ] Message sent successfully
- [ ] Message received on phone
- [ ] Status endpoint returns correct info
- [ ] Error handling for invalid numbers
- [ ] Rate limiting respected
- [ ] Cost tracking implemented

## Troubleshooting

### "Provider not configured" error
→ Set WHATSAPP_PROVIDER environment variable

### "Authentication failed"
→ Check API key/credentials are correct
→ Verify credentials haven't expired

### "Phone number not registered"
→ For Twilio sandbox: User must opt-in first
→ For production: Number must be opted-in to your business

### "Template not found"
→ Template must be approved by WhatsApp first
→ Check template name spelling

### "Message too long"
→ WhatsApp limit: 1600 characters
→ Split into multiple messages

### "24-hour window expired"
→ Must use approved template
→ Wait for user to message you again

## Production Checklist

- [ ] Business verified by Meta
- [ ] Phone number dedicated to WhatsApp Business
- [ ] Templates created and approved
- [ ] Privacy policy URL configured
- [ ] Rate limiting implemented (40-60 msg/second)
- [ ] Webhook endpoint for incoming messages
- [ ] Error handling and retries
- [ ] Cost monitoring and alerts
- [ ] User opt-out mechanism
- [ ] GDPR/data protection compliance

## Resources

- **Twilio Docs**: https://www.twilio.com/docs/whatsapp
- **360dialog Docs**: https://docs.360dialog.com/
- **MessageBird Docs**: https://developers.messagebird.com/
- **WhatsApp Business Policy**: https://www.whatsapp.com/legal/business-policy
- **Meta Business Verification**: https://business.facebook.com/

## Support

For issues with:
- **This implementation**: Check logs in demo mode
- **Provider setup**: Contact provider support
- **Business verification**: Meta Business Support
- **Template approval**: WhatsApp Business Support

---

**Pro Tip**: Start with Twilio Sandbox (free) to develop and test, then upgrade to production when ready.
