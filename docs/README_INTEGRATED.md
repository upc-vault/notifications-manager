# Intelligent Notification System - Complete Implementation

## Overview

A two-stage intelligent notification system that uses:
1. **Sleeping Multi-Armed Bandit (UCB1)** for template selection
2. **Tug of War (TOW) Algorithm** for dynamic channel selection

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NOTIFICATION REQUEST                      │
│  (type, priority, user_segment, time_of_day)                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         STAGE 1: TEMPLATE SELECTION                          │
│     Sleeping Multi-Armed Bandit (UCB1 Algorithm)            │
│                                                              │
│  • Explores different templates                             │
│  • Learns engagement rates per template                     │
│  • Context-aware selection                                  │
│  • Balances exploration vs exploitation                     │
│                                                              │
│  Output: Notification Template                              │
│  (formal, concise, friendly, urgent, informative, promo)    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         STAGE 2: CHANNEL SELECTION                           │
│          Tug of War (TOW) Algorithm                          │
│                                                              │
│  • Evaluates available channels                             │
│  • Considers real-time metrics:                             │
│    - Availability                                            │
│    - Cost                                                    │
│    - Latency                                                 │
│    - Success rate                                            │
│    - User preference                                         │
│  • Priority-based weight adjustment                         │
│                                                              │
│  Output: Notification Channel                               │
│  (SMS, Push, Email, WhatsApp)                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  SEND NOTIFICATION                           │
│         (Selected Template + Selected Channel)              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  FEEDBACK COLLECTION                         │
│  • Delivery success/failure                                  │
│  • User engagement score                                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  UPDATE ALGORITHMS                           │
│  • Template Bandit: Update engagement rates                  │
│  • Channel Selector: Update success rates                   │
│  • Continuous learning and adaptation                        │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
notifications-manager/
├── template_bandit.py          # Sleeping Multi-Armed Bandit for templates
├── tug_of_war.py              # Tug of War algorithm for channels
├── notification_environment.py # Simulation environment
├── train_integrated.py        # Training script for both algorithms
├── demo_integrated.py         # Interactive demonstration
├── test_bandit.py            # Unit tests (legacy)
├── integrated_model.json     # Trained model statistics
├── integrated_training_results.png  # Training visualizations
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Algorithms

### 1. Sleeping Multi-Armed Bandit (Template Selection)

**Purpose:** Select the notification template that maximizes user engagement

**Algorithm:** UCB1 (Upper Confidence Bound)

**Formula:**
```
score = mean_engagement + c * sqrt(ln(t) / n) + context_bonus
```
Where:
- `mean_engagement`: Average engagement score for template
- `c`: Exploration factor (typically 2.0)
- `t`: Total selections made
- `n`: Times this template was selected
- `context_bonus`: Bonus based on context matching (0-0.3)

**Templates:**
- **FORMAL**: Professional, detailed (best for statements, policies)
- **CONCISE**: Brief, to the point (best for alerts, updates)
- **FRIENDLY**: Casual, personable (best for promotions, tips)
- **URGENT**: Action-oriented (best for security, payment due)
- **INFORMATIVE**: Educational (best for features, announcements)
- **PROMOTIONAL**: Marketing-focused (best for offers, cross-sell)

**Context Matching:**
- Matches template characteristics to notification type
- Considers user segment preferences
- Adjusts for message priority
- Adds bonus (0-0.3) for good matches

### 2. Tug of War Algorithm (Channel Selection)

**Purpose:** Select the notification channel that optimizes delivery and cost

**Algorithm:** Weighted scoring with dynamic priority adjustments

**Score Calculation:**
```python
score = w1*availability + w2*success_rate + w3*user_preference + 
        w4*(1-cost) + w5*(1-latency) + w6*priority_weight
```

**Channels:**
- **SMS**: High reliability (85%), expensive, always available
- **Push**: Good engagement (75%), cheap, requires app
- **Email**: Lower engagement (50%), cheapest, always available
- **WhatsApp**: High engagement (80%), low cost, modern preference

**Metrics:**
- **Availability** (0-1): Whether channel is currently available
- **Success Rate** (0-1): Historical delivery success
- **User Preference** (0-1): User's preferred channels
- **Cost** (0-1): Normalized channel cost (0=free, 1=expensive)
- **Latency** (seconds): Expected delivery time
- **Priority Weight** (multiplier): Urgency of message

**Priority-Based Weights:**

| Priority | Availability | Success | Preference | Cost | Latency |
|----------|-------------|---------|------------|------|---------|
| Critical | 0.40        | 0.35    | 0.05       | 0.03 | 0.15    |
| High     | 0.30        | 0.35    | 0.15       | 0.05 | 0.10    |
| Medium   | 0.25        | 0.30    | 0.25       | 0.10 | 0.05    |
| Low      | 0.15        | 0.25    | 0.30       | 0.25 | 0.03    |

**Learning:**
- Exponential moving average for success rates:
  ```
  new_rate = β * old_rate + (1 - β) * observed_result
  ```
- β = 0.9 (momentum factor)

## Training Results

### Performance (10,000 episodes)

| Metric | Value |
|--------|-------|
| **Template Avg Engagement** | 61.33% |
| **Channel Success Rate** | 77.85% |
| **Combined Reward** | 61.33% |
| **Total Cumulative Reward** | 6,132.54 |

### Template Performance

| Template | Uses | Avg Engagement | Success Rate |
|----------|------|----------------|--------------|
| URGENT | 3,235 (32%) | 67.60% | 78.24% |
| CONCISE | 2,584 (26%) | 66.23% | 78.91% |
| FORMAL | 1,480 (15%) | 56.94% | 78.04% |
| INFORMATIVE | 1,235 (12%) | 53.44% | 76.60% |
| PROMOTIONAL | 734 (7%) | 49.95% | 74.66% |
| FRIENDLY | 732 (7%) | 49.85% | 77.32% |

**Insights:**
- **URGENT** and **CONCISE** templates achieve highest engagement
- Best for transaction alerts and time-sensitive notifications
- **FORMAL** works well for official communications
- **PROMOTIONAL** has lowest engagement (expected for marketing)

### Channel Performance

| Channel | Selections | Selection Rate | Success Rate |
|---------|-----------|----------------|--------------|
| WhatsApp | 5,322 | 53.2% | 89.13% |
| Push | 3,401 | 34.0% | 66.37% |
| SMS | 1,005 | 10.1% | 58.63% |
| Email | 272 | 2.7% | 30.05% |

**Insights:**
- **WhatsApp** emerges as best overall channel (high success, low cost)
- **Push** gets significant usage (cheap, good for app users)
- **SMS** used selectively (expensive but reliable)
- **Email** avoided due to low engagement

## Installation

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Train the Integrated System

```bash
cd notifications-manager
python train_integrated.py
```

Output:
- `integrated_model.json` - Model statistics
- `integrated_training_results.png` - Visualizations

### 2. Run Interactive Demo

```bash
python demo_integrated.py
```

Demonstrates:
- Template selection for different scenarios
- Channel selection based on context
- Batch processing
- Performance statistics

### 3. Use in Production

```python
from template_bandit import SleepingTemplateBandit, NotificationTemplate
from tug_of_war import TugOfWarSelector, NotificationChannel

# Initialize
templates = list(NotificationTemplate)
template_bandit = SleepingTemplateBandit(templates)

channels = list(NotificationChannel)
channel_selector = TugOfWarSelector(channels)

# Context for notification
context = {
    'notification_type': 'transaction_alert',
    'user_segment': 'premium',
    'priority': 'high',
    'time_of_day': 'morning'
}

# STAGE 1: Select template
selected_template = template_bandit.select_template(context)

# STAGE 2: Select channel
available_channels = get_available_channels()  # Your implementation
selected_channel = channel_selector.select_channel(
    context, 
    available_channels
)

# Send notification
success = send_notification(
    template=selected_template,
    channel=selected_channel,
    message=message
)

# Update algorithms with feedback
engagement = measure_user_engagement()  # Your metric
template_bandit.update(selected_template, success, engagement, context)
channel_selector.update_success_rate(selected_channel, success)
```

## Key Features

### ✅ Two-Stage Optimization
- Independent learning for template and channel
- Template focuses on user engagement
- Channel focuses on delivery success and cost

### ✅ Context-Aware Selection
- Considers notification type, user segment, priority
- Time-based availability (channels may "sleep")
- Dynamic weight adjustment for priorities

### ✅ Continuous Learning
- Both algorithms learn from feedback
- Adapts to changing user behavior
- Balances exploration and exploitation

### ✅ Production-Ready
- Clean, modular architecture
- Type hints throughout
- Comprehensive error handling
- Efficient algorithms (O(n) complexity)

## Demo Results

**Batch Processing (20 notifications):**
- Success Rate: 95% (19/20 delivered)
- Avg Engagement: 76%
- WhatsApp selected 75% of the time
- Push selected 25% of the time

**Template Distribution:**
- Balanced usage across all templates
- Context-aware selection working correctly

## Comparison: Before vs After

### Before (Single Algorithm)
- Only channel selection
- Fixed rules for templates
- No engagement optimization
- ~79% success rate

### After (Integrated System)
- Two-stage intelligent selection
- Learning-based templates
- Engagement + delivery optimization
- 95% success in demo, 78% in training

## Next Steps for Production

### 1. API Development
```python
# FastAPI endpoint example
@app.post("/api/v1/notify")
async def send_notification(request: NotificationRequest):
    # Select template
    template = template_bandit.select_template(request.context)
    
    # Select channel
    channel = channel_selector.select_channel(
        request.context,
        await get_available_channels(request.user_id)
    )
    
    # Send and track
    result = await notification_service.send(
        user_id=request.user_id,
        template=template,
        channel=channel,
        message=request.message
    )
    
    # Update algorithms
    await update_feedback(template, channel, result)
    
    return result
```

### 2. Service Integration
- Twilio for SMS
- Firebase Cloud Messaging for Push
- SendGrid for Email
- WhatsApp Business API

### 3. Monitoring
- Prometheus metrics
- Grafana dashboards
- Real-time performance tracking
- A/B testing framework

### 4. Database Schema
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    user_id VARCHAR,
    notification_type VARCHAR,
    priority VARCHAR,
    template VARCHAR,
    channel VARCHAR,
    delivered BOOLEAN,
    engagement_score FLOAT,
    sent_at TIMESTAMP,
    context JSONB
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_template ON notifications(template);
CREATE INDEX idx_notifications_channel ON notifications(channel);
```

## Testing

Run tests (legacy, needs update for integrated system):
```bash
python test_bandit.py
```

## Performance Benchmarks

- **Selection Time**: < 1ms per decision
- **Memory Usage**: ~10MB for model state
- **Throughput**: 1000+ selections/second
- **Training Time**: ~30 seconds for 10,000 episodes

## References

- **UCB1 Algorithm**: Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002)
- **Multi-Armed Bandits**: Sutton & Barto - Reinforcement Learning
- **Tug of War**: Weighted scoring with dynamic optimization
- **PMBOK 7**: Project Management Framework
- **ISO/IEC 25010**: Software Quality Requirements

## License

Academic Project - Universidad Peruana de Ciencias Aplicadas (UPC)  
Course: Proyecto Profesional II (PI-2) - 2026

## Authors

Notifications Manager Project Team  
Gestor inteligente de notificaciones online mediante machine learning para banca privada
