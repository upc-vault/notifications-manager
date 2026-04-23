# Sleeping Multi-Armed Bandit for Notification Channel Selection

An intelligent notification channel selection system using reinforcement learning (Sleeping Multi-Armed Bandit algorithm) for banking applications.

## Overview

This implementation solves the problem of selecting the optimal notification channel (SMS, Push, Email, WhatsApp) in real-time, considering:
- **Channel availability** (some channels may not be available at certain times - "sleeping arms")
- **Time-based patterns** (morning, afternoon, evening, night)
- **User segments** (standard, premium, young users)
- **Success rates** (delivery and engagement rates)

## Project Structure

```
notifications-manager/
├── sleeping_bandit.py           # Core bandit algorithms (UCB1, Epsilon-Greedy)
├── notification_environment.py  # Simulation environment
├── train_bandit.py             # Training script
├── test_bandit.py              # Unit tests
├── __init__.py                 # Package initialization
├── trained_bandit_model.json   # Trained model statistics
└── training_results.png        # Training visualization
```

## Key Components

### 1. Sleeping Bandit (`sleeping_bandit.py`)

Implements two algorithms:

#### **UCB1 (Upper Confidence Bound)**
- Balances exploration and exploitation
- Uses confidence intervals to make decisions
- Formula: `UCB = mean_reward + c * sqrt(ln(t) / n)`
- Best for: Long-term performance optimization

#### **Epsilon-Greedy**
- Simple exploration strategy
- Explores randomly with probability ε (0.1)
- Exploits best known arm with probability 1-ε
- Best for: Quick convergence, simpler interpretation

### 2. Notification Environment (`notification_environment.py`)

Simulates realistic banking notification scenarios:

**Channel Success Rates (baseline):**
- **SMS**: 85% (reliable but costly)
- **WhatsApp**: 80% (high engagement)
- **Push Notifications**: 75% (depends on app usage)
- **Email**: 50% (often ignored)

**Context Factors:**
- Time of day affects engagement
- User segment affects preferences
- Channel availability varies

### 3. Banking Scenarios

Predefined notification types:
- **Transaction Alerts** (critical, immediate)
- **Security Alerts** (critical, <30s)
- **Account Statements** (medium priority)
- **Promotional Offers** (low priority)

## Training Results

### Performance (10,000 episodes)

| Algorithm | Total Reward | Avg Reward | Best Channel |
|-----------|-------------|------------|--------------|
| **UCB1** | 7,949 | 0.7949 | WhatsApp (81.08%) |
| **Epsilon-Greedy** | 7,980 | 0.7980 | SMS (81.51%) |

### Channel Selection Distribution (UCB1)

- **WhatsApp**: 4,127 selections (41.27%)
- **SMS**: 4,022 selections (40.22%)
- **Push**: 1,675 selections (16.75%)
- **Email**: 176 selections (1.76%)

The algorithm learned to:
1. **Prefer high-success channels** (WhatsApp, SMS)
2. **Avoid low-performing channels** (Email - only 1.76% usage)
3. **Balance exploration** (tried all channels to learn their rates)

## Installation

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install numpy matplotlib
```

## Usage

### 1. Run Tests

```bash
cd notifications-manager
python test_bandit.py
```

Expected output: **22 tests passed**

### 2. Train the Model

```bash
python train_bandit.py
```

This will:
- Train both UCB1 and Epsilon-Greedy algorithms
- Generate visualizations (`training_results.png`)
- Save model statistics (`trained_bandit_model.json`)

### 3. Use in Production

```python
from sleeping_bandit import SleepingBandit, NotificationChannel
from notification_environment import NotificationEnvironment

# Initialize
channels = list(NotificationChannel)
bandit = SleepingBandit(channels=channels, exploration_factor=2.0)
env = NotificationEnvironment()

# Select channel for notification
time_of_day = 'morning'
available_channels = env.get_available_channels(time_of_day)
selected_channel = bandit.select_channel(available_channels)

# Send notification via selected_channel...
# (integration with actual notification services)

# Update with result
reward = 1.0 if notification_delivered_and_read else 0.0
bandit.update(selected_channel, reward, available_channels)
```

## Key Features

### 1. **Sleeping Arms Handling**
Not all channels are always available (e.g., push notifications require active app). The algorithm only selects from available channels.

### 2. **Context-Aware Selection**
- Time of day affects availability and success
- User segments have different preferences
- Real-time adaptation to patterns

### 3. **Exploration vs Exploitation**
- UCB1: Automatic balance via confidence bounds
- Epsilon-Greedy: Fixed 10% exploration rate

### 4. **Performance Tracking**
- Success rates per channel
- Cumulative rewards
- Selection distribution
- Historical data for analysis

## Algorithm Details

### UCB1 Formula

```python
score = mean_reward + c * sqrt(ln(total_time) / arm_pulls)
```

Where:
- `mean_reward`: Empirical success rate
- `c`: Exploration factor (typically √2)
- `total_time`: Total episodes
- `arm_pulls`: Times this arm was selected

### Why UCB1?

1. **Theoretical guarantees**: Logarithmic regret bound
2. **No hyperparameters to tune**: Self-adjusting
3. **Efficient exploration**: Focuses on uncertain arms
4. **Works with sleeping arms**: Only considers available channels

## Testing

Comprehensive test suite covering:
- ✅ Arm initialization and updates
- ✅ UCB score calculation
- ✅ Channel selection logic
- ✅ Environment simulation
- ✅ Reward generation
- ✅ Integration tests
- ✅ Learning convergence

## Future Enhancements

1. **Contextual Bandit**: Include user features (age, location, device)
2. **Thompson Sampling**: Bayesian approach for better exploration
3. **Batch Updates**: Process multiple notifications efficiently
4. **Cost Optimization**: Consider per-channel costs (SMS is expensive)
5. **A/B Testing Integration**: Compare against baseline strategies
6. **Real-time Drift Detection**: Adapt to changing user behavior

## Performance Metrics

### Key Metrics Tracked

- **Success Rate**: % of successful notifications per channel
- **Cumulative Reward**: Total successful deliveries
- **Regret**: Difference from optimal strategy
- **Channel Utilization**: Selection frequency per channel

### Convergence

Both algorithms converge within ~2,000-3,000 episodes, after which performance stabilizes around 79-80% average success rate.

## Banking Context

This implementation aligns with the research project requirements:

- ✅ **Multi-channel unification**: Manages SMS, Push, Email, WhatsApp
- ✅ **Machine Learning**: Reinforcement learning for optimization
- ✅ **Real-time selection**: Sub-millisecond decision making
- ✅ **Traceability**: Complete history of decisions and outcomes
- ✅ **Personalization**: Context-aware channel selection
- ✅ **Scalability**: Efficient algorithm suitable for high volumes

## References

- **PMBOK 7th Edition**: Project management framework
- **ISO/IEC 25010**: Software quality requirements
- **Ley N° 29733**: Data protection compliance (Peru)
- **Resolución SBS 504-2021**: Banking cybersecurity standards

## License

Academic project - Universidad Peruana de Ciencias Aplicadas (UPC)
PI2 - Notifications Manager - 2026

## Authors

Project: Gestor inteligente de notificaciones online mediante machine learning para banca privada
Course: Proyecto Profesional II (PI-2)
