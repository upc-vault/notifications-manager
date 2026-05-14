# Intelligent Notification Manager - ML with User Profiles

**Personalized notification delivery using Machine Learning algorithms trained on user profiles, preferences, and behavioral patterns.**

## Overview

This notification manager uses two ML algorithms to intelligently select the best **notification template** and **delivery channel** for each individual user:

1. **Sleeping Multi-Armed Bandit**: Selects optimal message template based on user profile and historical engagement
2. **Tug of War (TOW)**: Dynamically chooses the best delivery channel based on user preferences and performance

### 🎯 Key Features

✨ **User Profile-Based Learning**: Personalized for age, banking tier, digital adoption  
✨ **Preference Enforcement**: Respects opt-outs, channel preferences, notification times  
✨ **Behavioral Adaptation**: Learns from open rates, click rates, engagement history  
✨ **Real-Time Updates**: Continuous learning from user interactions  
✨ **Multi-Channel Support**: Push, Email, SMS, WhatsApp, WebPush  
✨ **Banking Tier Awareness**: Different strategies for Natural, Prime, Private, Patrimonial

## Training Results

See [TRAINING_RESULTS.md](TRAINING_RESULTS.md) for comprehensive analysis.

### User-Specific Performance

| User Profile | Age | Tier | Digital | Avg Reward | Open Rate | Best Channel |
|--------------|-----|------|---------|------------|-----------|--------------|
| Ana Jimenez | 22 | Natural | 95% | **0.451** | **44.94%** | Push (52.46%) |
| Carlos Mendez | 28 | Prime | 90% | 0.327 | 33.18% | SMS (15.09%) |
| Maria Rodriguez | 45 | Private | 70% | 0.286 | 29.12% | WhatsApp (49.48%) |
| Luis Torres | 38 | Prime | 75% | 0.202 | 20.83% | Push |
| Roberto Silva | 68 | Patrimonial | 40% | 0.232 | 25.00% | SMS (52.98%) |

### Key Insights

🎯 **Young tech-savvy users** achieve 2x better engagement (44.94% vs 20.83%)  
🎯 **Private banking clients** prefer WhatsApp (49.48% success)  
🎯 **Senior users** respond best to SMS (52.98% success)  
🎯 **Personalization impact**: Up to 220% improvement in open rates

## Installation

```bash
# Install dependencies
pip install numpy matplotlib

# Run training with user profiles
python train_algorithms.py
```

## Quick Start

### Complete Example with User Profile

```python
from notifications_manager import (
    SleepingMultiArmedBandit, Template,
    TugOfWarChannelSelector, Channel,
    UserProfile, UserPreferences, BankingTier,
)

# 1. Create or load user profile
user = UserProfile(
    user_id="user_123",
    name="Ana Jimenez",
    age=25,
    banking_tier=BankingTier.PRIME,
    preferences=UserPreferences(
        preferred_channels=["push", "whatsapp"],
        marketing_opt_in=True,
    ),
    digital_adoption=0.9,
    device_type="mobile"
)

# 2. Initialize algorithms (personalized per user)
templates = [
    Template("urgent", "Urgent Alert", "¡Transferencia detectada!"),
    Template("security", "Security Alert", "Nuevo inicio de sesión"),
]
bandit = SleepingMultiArmedBandit(templates)

channels = [Channel.PUSH, Channel.EMAIL, Channel.WHATSAPP]
tow = TugOfWarChannelSelector(channels)

# 3. Select template with user affinity
selected_template_id = bandit.select_template()
template_affinity = user.get_template_affinity(selected_template_id)

# 4. Select channel with user preference
selected_channel = tow.select_channel()
channel_affinity = user.get_channel_affinity(selected_channel.value)

# 5. Send notification
success = send_notification(user, selected_template_id, selected_channel)
opened = user_opened_notification()
clicked = user_clicked_notification()

# 6. Calculate reward
reward = 1.0 if clicked else (0.6 if opened else (0.3 if success else 0.0))

# 7. Update algorithms
bandit.update_reward(selected_template_id, reward)
tow.update_result(selected_channel, success)

# 8. Update user behavior for continuous learning
user.update_behavior(selected_template_id, selected_channel.value, opened, clicked)
```

### User Profile System

```python
from notifications_manager import UserProfile, UserPreferences, BankingTier

user = UserProfile(
    user_id="user_123",
    name="Ana Jimenez",
    age=22,
    banking_tier=BankingTier.PRIME,
    
    # Demographics
    income_level="medium",
    digital_adoption=0.95,  # 0-1 scale
    device_type="mobile",
    
    # Preferences
    preferences=UserPreferences(
        preferred_channels=["push", "whatsapp"],
        marketing_opt_in=True,
        push_enabled=True,
    ),
)

# Check channel affinity
affinity = user.get_channel_affinity("push")  # Returns 0-1
template_affinity = user.get_template_affinity("template_security")
```

## Architecture

```
┌─────────────────────────────────────────┐
│  Notification Request + User ID         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Load User Profile                      │
│  • Demographics, Preferences, Behavior  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Sleeping Bandit (Template Selection)   │
│  • User affinity-weighted selection     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Tug of War (Channel Selection)         │
│  • Preference-aware selection           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Send Notification                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Update Algorithms & User Behavior      │
└─────────────────────────────────────────┘
```

## Project Structure

```
notifications-manager/
├── __init__.py                 # Package initialization
├── sleeping_bandit.py          # Sleeping Multi-Armed Bandit
├── tug_of_war.py              # Tug of War channel selector
├── user_profile.py            # User profile & behavioral tracking
├── train_algorithms.py        # Training script with profiles
├── README.md                  # This file
├── TRAINING_RESULTS.md        # Detailed analysis
├── bandit_stats.json          # Per-user statistics
├── tow_stats.json             # Channel statistics
├── user_profiles.json         # Learned behaviors
└── training_results.png       # Visualizations
```

## Reward System

| Event | Reward | Description |
|-------|--------|-------------|
| **Click/Action** | 1.0 | User took action |
| **Open** | 0.6 | User viewed notification |
| **Delivered** | 0.3 | Successfully delivered |
| **Failed** | 0.0 | Failed or ignored |

## Best Practices

### 1. Profile Management
- Keep user profiles updated
- Track behavioral changes continuously
- Respect opt-out preferences immediately

### 2. Personalization
- Check user affinities before sending
- Combine template + channel affinities
- Update user behavior after each notification

### 3. Privacy & Compliance
- Honor marketing opt-outs (Ley N° 28493)
- Respect frequency limits (default: 5/day)
- Implement channel disabling per request

## References

UPC Thesis Project - "Gestor inteligente de notificaciones online mediante machine learning para banca privada"  
Authors: Wilmer Quispe, Moises Lagos | Institution: BBVA Continental | Year: 2025-2026

---

**For detailed training results and analysis, see [TRAINING_RESULTS.md](TRAINING_RESULTS.md)**
