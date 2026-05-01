# Notifications Manager - Refactored

## ✨ New Improved Architecture

This project has been **refactored for better organization and maintainability**.

### What Changed?

1. **Modular Blueprints** - Split 680-line `app.py` into focused modules
2. **Configuration Management** - Dev/Prod/Test configs
3. **Extracted JavaScript** - Separate `.js` files
4. **Better Structure** - Clear separation of concerns

### Quick Start

```bash
# Use refactored version (recommended)
python scripts/start_api_refactored.py

# Or original version
python scripts/start_api.py
```

### New Structure

```
src/notifications_manager/api/
├── routes/              # Modular blueprints
│   ├── webpush.py       # WebPush endpoints
│   ├── templates.py     # Template management
│   ├── analytics.py     # Analytics
│   └── notifications.py # Notifications & ML
└── app_refactored.py    # Clean main app (220 lines)

config/                  # Configuration
├── development.py
├── production.py
└── testing.py

static/
├── js/                  # Extracted JavaScript
│   └── dashboard.js
└── css/                 # Ready for styles
```

### Features

- ✅ **680 lines** → **220 lines** main app
- ✅ **5 focused** blueprint modules
- ✅ **Environment-based** configuration
- ✅ **Extracted** JavaScript
- ✅ **Ready for** microservices

### Documentation

See [REFACTORING.md](REFACTORING.md) for complete details.

### Migration

Both versions work side-by-side. Test the refactored version, then update your scripts:

```python
# Update scripts/start_api.py
from src.notifications_manager.api.app_refactored import create_app
```

---

**Built with:** Python, Flask, Redis, SQLite, ML (Sleeping Bandit + Tug of War)
