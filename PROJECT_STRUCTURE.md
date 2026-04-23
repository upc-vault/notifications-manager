# Project Structure

```
notifications-manager/
│
├── 📁 src/
│   └── 📁 notifications_manager/          # Main Python package
│       ├── 📁 algorithms/                  # ML Algorithms
│       │   ├── template_bandit.py         # ✅ Sleeping Multi-Armed Bandit
│       │   ├── tug_of_war.py             # ✅ Tug of War Algorithm
│       │   ├── sleeping_bandit.py        # (Legacy reference)
│       │   └── __init__.py
│       ├── 📁 models/                      # Data models
│       │   └── __init__.py
│       ├── 📁 services/                    # Business logic
│       │   └── __init__.py
│       ├── 📁 utils/                       # Utilities
│       │   ├── notification_environment.py # Simulation environment
│       │   └── __init__.py
│       └── __init__.py
│
├── 📁 scripts/                             # Training & Demo
│   ├── train_integrated.py                # ⭐ Main training script
│   ├── demo_integrated.py                 # ⭐ Interactive demo
│   ├── train_bandit.py                    # (Legacy training)
│   └── demo_bandit.py                     # (Legacy demo)
│
├── 📁 tests/                               # Unit tests
│   └── test_bandit.py                     # Test suite
│
├── 📁 models/                              # 🎯 Trained Models & Results
│   ├── integrated_model.json              # ✅ Model statistics
│   ├── integrated_training_results.png    # ✅ 6 visualization plots
│   ├── trained_bandit_model.json          # (Legacy model)
│   └── training_results.png               # (Legacy visualizations)
│
├── 📁 docs/                                # 📚 Documentation
│   ├── 📁 api/
│   │   └── api.raml                       # API specifications
│   ├── 📁 esb/
│   │   └── README.md                      # ESB documentation
│   ├── README_INTEGRATED.md               # Technical docs
│   ├── IMPLEMENTATION_SUMMARY.md          # Implementation details
│   └── PI1_Trabajo de Investigación 2025-02-2.pdf  # Research paper (162 pages)
│
├── 📁 notebooks/                           # Jupyter notebooks (optional)
│
├── 📄 requirements.txt                     # Python dependencies
├── 📄 pyproject.toml                       # Project configuration
├── 📄 README.md                            # Main documentation
├── 📄 extract_pdf.py                       # PDF extraction utility
│
└── 📁 .venv/                               # Virtual environment

```

## 📊 Training Results Summary

### ✅ System Performance (10,000 Episodes)

| Component | Metric | Result |
|-----------|--------|--------|
| **Template Bandit** | Avg Engagement | 61.33% |
| **Channel Selector** | Success Rate | 77.85% |
| **Combined System** | Total Reward | 6,132.54 |
| **Demo Performance** | Success Rate | 95% |

### 🏆 Best Performing Components

**Templates**:
1. 🥇 **URGENT** - 67.60% engagement (3,235 uses)
2. 🥈 **CONCISE** - 66.23% engagement (2,584 uses)  
3. 🥉 **FORMAL** - 56.94% engagement (1,480 uses)

**Channels**:
1. 🥇 **WhatsApp** - 89.13% success (5,322 selections, 53.2%)
2. 🥈 **Push** - 66.37% success (3,401 selections, 34.0%)
3. 🥉 **SMS** - 58.63% success (1,005 selections, 10.1%)

### 📈 Key Metrics from integrated_model.json

```json
{
  "timestamp": "2026-04-22T22:53:21",
  "num_episodes": 10000,
  
  "template_statistics": {
    "urgent": {
      "total_pulls": 3235,
      "success_rate": 0.7824,
      "avg_engagement": 0.6760
    },
    "concise": {
      "total_pulls": 2584,
      "success_rate": 0.7891,
      "avg_engagement": 0.6623
    }
  },
  
  "channel_statistics": {
    "whatsapp": {
      "success_rate": 0.8913,
      "selections": 5322,
      "selection_rate": 0.5322
    },
    "push": {
      "success_rate": 0.6637,
      "selections": 3401,
      "selection_rate": 0.3401
    }
  },
  
  "performance_metrics": {
    "avg_template_engagement": 0.6133,
    "avg_channel_success": 0.7785,
    "total_cumulative_reward": 6132.54
  }
}
```

### 📊 Visualizations

**File**: `models/integrated_training_results.png`

Contains 6 comprehensive plots:
1. **Cumulative Reward Over Time** - Shows learning progression
2. **Template Engagement (MA-100)** - Moving average of engagement scores
3. **Channel Success Rate (MA-100)** - Moving average of delivery success
4. **Template Selection Distribution** - Bar chart of template usage
5. **Channel Selection Distribution** - Bar chart of channel usage (TOW)
6. **Combined Performance (MA-100)** - Overall system effectiveness

---

## 🎯 Project Organization Summary

✅ **Algorithms**: Properly separated in `src/notifications_manager/algorithms/`
✅ **Scripts**: Training and demo scripts in `scripts/`
✅ **Tests**: Unit tests in `tests/`
✅ **Models**: Trained models and visualizations in `models/`
✅ **Docs**: Complete documentation in `docs/`
✅ **Structure**: Professional package layout following Python best practices

## 🚀 Quick Commands

```bash
# Train the system
python scripts/train_integrated.py

# Run demo
python scripts/demo_integrated.py

# Run tests
python -m pytest tests/

# View results
explorer models\integrated_training_results.png
```

---

**Status**: ✅ **TRAINING COMPLETE & ORGANIZED**
**Date**: April 22, 2026
**Institution**: UPC - Universidad Peruana de Ciencias Aplicadas
