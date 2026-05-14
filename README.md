# Intelligent Notification Manager

**Sistema Gestor Inteligente de Notificaciones Online mediante Machine Learning para Banca Privada**

## Descripción del Proyecto

Sistema de gestión inteligente de notificaciones para banca privada que utiliza algoritmos de Machine Learning para optimizar la selección de plantillas de mensajes y canales de entrega, maximizando el engagement del usuario mientras respeta sus preferencias y cumple con regulaciones peruanas.

### 🎯 Características Principales

- **Selección Inteligente de Plantillas**: Sleeping Multi-Armed Bandit personalizado por perfil de usuario
- **Optimización de Canales**: Tug of War para selección dinámica de canal (Push, Email, SMS, WhatsApp, WebPush)
- **Personalización**: Basado en perfiles demográficos, preferencias y comportamiento histórico
- **Multi-Canal**: Integración con Firebase, APNs, Amazon SES, WhatsApp Business API
- **Cumplimiento Normativo**: Ley N° 28493 (anti-spam), SBS Resolución 504-2021
- **Arquitectura Microservicios**: Escalable y modular

## 📊 Resultados del Training

### Rendimiento por Perfil de Usuario

| Usuario | Edad | Tier | Adopción Digital | Recompensa Promedio | Tasa Apertura | Mejor Canal |
|---------|------|------|------------------|---------------------|---------------|-------------|
| **Ana Jimenez** | 22 | Natural | 95% | **0.451** | **44.94%** | Push (52.46%) |
| Carlos Mendez | 28 | Prime | 90% | 0.327 | 33.18% | SMS (15.09%) |
| Maria Rodriguez | 45 | Private | 70% | 0.286 | 29.12% | WhatsApp (49.48%) |
| Luis Torres | 38 | Prime | 75% | 0.202 | 20.83% | Push |
| Roberto Silva | 68 | Patrimonial | 40% | 0.232 | 25.00% | SMS (52.98%) |

### Insights Clave

🎯 **Usuarios jóvenes tech-savvy** logran 2x mejor engagement (44.94% vs 20.83%)  
🎯 **Clientes Private Banking** prefieren **WhatsApp** (49.48% éxito)  
🎯 **Usuarios seniors** responden mejor a **SMS** (52.98% éxito)  
🎯 **Impacto de personalización**: Hasta 220% de mejora en tasas de apertura

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                   API Gateway (REST/GraphQL)            │
│                    Puerto: 8000                         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│  User Service │         │ Auth Service  │
│  (Profiles)   │         │  (JWT/OAuth)  │
└───────┬───────┘         └───────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│     Notification Service (Core)         │
│  • Request validation                   │
│  • User profile loading                 │
│  • ML algorithm orchestration           │
└────────────────┬────────────────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Bandit  │ │ TOW     │ │ User    │
│ ML      │ │ ML      │ │ Behavior│
│Template │ │ Channel │ │ Tracker │
└────┬────┘ └────┬────┘ └─────────┘
     │           │
     └─────┬─────┘
           │
           ▼
┌─────────────────────────────────────────┐
│       Provider Abstraction Layer        │
│  • Retry logic                          │
│  • Rate limiting                        │
│  • Error handling                       │
└────────────────┬────────────────────────┘
                 │
     ┌───────────┼───────────────────┐
     │           │           │        │
     ▼           ▼           ▼        ▼
┌─────────┐ ┌─────────┐ ┌───────┐ ┌──────────┐
│Firebase │ │  APNs   │ │  SES  │ │WhatsApp  │
│  (Push) │ │ (iOS)   │ │(Email)│ │Business  │
└─────────┘ └─────────┘ └───────┘ └──────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│          MongoDB (Traceability)         │
│  • Notification logs                    │
│  • User interactions                    │
│  • ML model stats                       │
└─────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
notifications-manager/
├── src/
│   ├── api/                    # REST API endpoints
│   │   ├── routes/            # Route definitions
│   │   ├── middleware/        # Auth, validation, logging
│   │   └── schemas/           # Request/response schemas
│   ├── services/              # Business logic
│   │   ├── notification_service.py
│   │   ├── user_service.py
│   │   └── analytics_service.py
│   ├── ml/                    # Machine Learning algorithms
│   │   ├── sleeping_bandit.py # Template selection
│   │   ├── tug_of_war.py     # Channel selection
│   │   └── __init__.py
│   ├── models/                # Data models
│   │   ├── user_profile.py   # User profile & behavior
│   │   ├── notification.py   # Notification models
│   │   └── template.py       # Template models
│   ├── providers/             # Channel providers
│   │   ├── push_provider.py  # Firebase/APNs
│   │   ├── email_provider.py # Amazon SES
│   │   ├── sms_provider.py   # Twilio/AWS SNS
│   │   └── whatsapp_provider.py
│   └── utils/                 # Utilities
│       ├── validators.py     # Anti-XSELL validation
│       ├── logger.py         # Logging setup
│       └── db.py             # Database connection
├── config/                    # Configuration files
│   ├── settings.py           # App settings
│   ├── database.py           # DB config
│   └── providers.yaml        # Provider credentials
├── scripts/                   # Utility scripts
│   ├── train_algorithms.py   # ML training script
│   └── migrate_db.py         # Database migrations
├── tests/                     # Unit & integration tests
│   ├── test_ml/
│   ├── test_services/
│   └── test_providers/
├── data/                      # Data files
│   └── training/             # Training results
│       ├── bandit_stats.json
│       ├── tow_stats.json
│       ├── user_profiles.json
│       └── training_results.png
├── docs/                      # Documentation
│   ├── ML_README.md          # ML algorithms docs
│   ├── TRAINING_RESULTS.md   # Training analysis
│   └── API.md                # API documentation
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker services
└── README.md                 # This file
```

## 🚀 Instalación y Setup

### Requisitos Previos

- Python 3.10+
- MongoDB 5.0+
- Docker & Docker Compose (opcional)
- Cuentas en: Firebase, AWS SES, Twilio, WhatsApp Business API

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd notifications-manager
```

### 2. Configurar Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\activate  # Windows
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 5. Entrenar Algoritmos ML

```bash
python scripts/train_algorithms.py
```

### 6. Iniciar Servicios

```bash
# Con Docker
docker-compose up -d

# Sin Docker
python src/api/main.py
```

## 📊 Ver Resultados del Training

### Visualización Gráfica

```bash
# Abrir imagen de resultados
start data/training/training_results.png  # Windows
# o
open data/training/training_results.png  # Mac/Linux
```

### Estadísticas JSON

```bash
# Ver estadísticas del Bandit
cat data/training/bandit_stats.json | python -m json.tool

# Ver estadísticas de TOW
cat data/training/tow_stats.json | python -m json.tool

# Ver perfiles de usuario aprendidos
cat data/training/user_profiles.json | python -m json.tool
```

## 🔧 Uso del Sistema

### Ejemplo: Enviar Notificación

```python
from src.services.notification_service import NotificationService
from src.models.user_profile import UserProfile

# Inicializar servicio
service = NotificationService()

# Crear/cargar perfil de usuario
user = UserProfile.load("user_123")

# Enviar notificación (sistema selecciona template y canal automáticamente)
result = service.send_notification(
    user_id="user_123",
    message_type="security",  # Sugerencia de tipo
    data={
        "amount": "1500.00",
        "transaction_id": "TXN12345"
    }
)

print(f"Enviado vía: {result.channel}")
print(f"Template usado: {result.template}")
print(f"Estado: {result.status}")
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest tests/

# Tests específicos
pytest tests/test_ml/
pytest tests/test_services/

# Con cobertura
pytest --cov=src tests/
```

## 📈 Monitoreo y Métricas

### Métricas Clave

- **Tasa de Apertura**: % de notificaciones abiertas
- **Tasa de Click**: % de notificaciones con acción
- **Tasa de Entrega**: % de entregas exitosas
- **Tiempo de Respuesta**: Latencia del sistema
- **Engagement Score**: Recompensa promedio por usuario

### Dashboard

Acceder a métricas en tiempo real:
```
http://localhost:8000/dashboard
```

## 🛡️ Cumplimiento Normativo

### Ley N° 28493 (Anti-Spam)

✅ Opt-in explícito para marketing  
✅ Opt-out en cada mensaje  
✅ Límites de frecuencia configurables  
✅ Respeto a preferencias de canal

### SBS Resolución 504-2021

✅ Trazabilidad completa de notificaciones  
✅ Auditoría de cambios  
✅ Encriptación de datos sensibles  
✅ Segregación por nivel de seguridad

## 🏆 Mejores Prácticas

### 1. Segmentación de Usuarios
- Crear perfiles detallados con datos demográficos
- Actualizar preferencias en tiempo real
- Respetar opt-outs inmediatamente

### 2. Entrenamiento Continuo
- Re-entrenar modelos semanalmente
- Monitorear drift en performance
- A/B testing de nuevas estrategias

### 3. Optimización de Canales
- Probar canales emergentes (WhatsApp Business)
- Failover automático si canal falla
- Rate limiting por proveedor

## 📚 Referencias

- **Tesis**: "Gestor inteligente de notificaciones online mediante machine learning para banca privada"
- **Autores**: Wilmer Andres Quispe Gomez, Moises Jhonatan Lagos Pachas
- **Institución**: Universidad Peruana de Ciencias Aplicadas (UPC)
- **Cliente**: BBVA Continental
- **Año**: 2025-2026

## 📄 Licencia

Proyecto educativo - UPC PI2 2025-2026

## 👥 Equipo

- **Wilmer Andres Quispe Gomez** - ML & Backend
- **Moises Jhonatan Lagos Pachas** - Architecture & Integration

## 📞 Soporte

Para consultas sobre el proyecto: [Contacto UPC]

---

**Documentación adicional:**
- [ML Algorithms](docs/ML_README.md)
- [Training Results](docs/TRAINING_RESULTS.md)
- [API Documentation](docs/API.md)
