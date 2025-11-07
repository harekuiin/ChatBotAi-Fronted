# Microservicio OpenAI - RAG Chat API

Microservicio independiente para integración con frontends y otros microservicios.

## 🚀 Características

- API REST con FastAPI
- Sistema RAG (Retrieval-Augmented Generation)
- Chat con memoria conversacional
- Streaming de respuestas en tiempo real
- Soporte para documentos TXT y SVG
- Guardrails médicos configurables
- CORS configurado para integración

## 📋 Instalación Rápida

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar variables de entorno:**
```bash
# Copiar el archivo de ejemplo
copy env.example .env

# Editar .env y agregar tu OPENAI_API_KEY
OPENAI_API_KEY=tu-clave-aqui
```

3. **Ejecutar el microservicio:**
```bash
python run.py
```

El servidor estará disponible en: `http://localhost:8000`

## 🔌 Endpoints Principales

- `GET /` - Health check básico
- `GET /health` - Estado detallado de servicios
- `POST /chat` - Chat básico (sin memoria)
- `POST /coach` - Plan de coaching personalizado
- `POST /coach/stream` - Chat con streaming y memoria
- `GET /documents/list` - Listar documentos
- `POST /documents/upload` - Subir documentos
- `POST /documents/reload` - Recargar documentos

## 📚 Documentación Interactiva

Una vez ejecutando, accede a:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 Configuración

Edita el archivo `.env` para configurar:

- `OPENAI_API_KEY` - **OBLIGATORIO** - Tu clave de API de OpenAI
- `OPENAI_MODEL` - Modelo de chat (default: gpt-3.5-turbo-0125)
- `KB_DIRECTORY` - Directorio de documentos (default: ./kb)
- `SERVICE_PORT` - Puerto del servidor (default: 8000)
- `ENABLE_MEDICAL_GUARDRAILS` - Activar guardrails (default: true)

## 📁 Estructura

```
Microservicio_Openai/
├── app/
│   ├── __init__.py
│   ├── main.py              # Endpoints FastAPI
│   ├── config.py            # Configuración
│   ├── models.py            # Modelos de datos
│   ├── rag_service.py       # Servicio RAG básico
│   ├── chat_service.py      # Servicio de chat avanzado
│   ├── document_processor.py # Procesador de documentos
│   └── guardrails.py        # Guardrails médicos
├── kb/                      # Directorio de documentos (se crea automáticamente)
├── requirements.txt         # Dependencias
├── run.py                   # Script de inicio
├── env.example              # Ejemplo de configuración
└── README.md               # Este archivo
```

## 🔗 Integración con Frontend

El microservicio tiene CORS configurado para aceptar conexiones desde cualquier origen. Para integrarlo:

```javascript
const API_URL = 'http://localhost:8000';

// Ejemplo: Chat con streaming
fetch(`${API_URL}/coach/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: "Tu pregunta aquí",
        conversation_id: "user-123"
    })
});
```

## 🔗 Integración con Otros Microservicios

El microservicio puede ser llamado desde otros servicios mediante HTTP:

```python
import requests

response = requests.post(
    'http://localhost:8000/coach',
    json={
        "user_profile": {...},
        "risk_score": 0.65,
        "top_drivers": ["bmi", "waist"]
    }
)
```

## 📝 Notas

- Los documentos se cargan desde el directorio `kb/`
- El vector store se crea automáticamente en `chroma_db/`
- La memoria conversacional se mantiene por `conversation_id`
- Los guardrails médicos son configurables vía `.env`

## 🛠️ Tecnologías

- FastAPI
- LangChain
- OpenAI
- ChromaDB
- Pydantic

---

**Versión:** 1.0.0  
**Autor:** Hackathon Salud NHANES 2025


