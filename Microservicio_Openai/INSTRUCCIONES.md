# 📋 Instrucciones de Uso - Microservicio OpenAI

## 🎯 Propósito

Este microservicio es una versión independiente y portable del backend, lista para:
- Integración con cualquier frontend
- Conexión con otros microservicios
- Despliegue independiente
- Reutilización en otros proyectos

## ⚡ Inicio Rápido

### 1. Instalar Dependencias
```bash
cd Microservicio_Openai
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
copy env.example .env

# Editar .env y agregar tu API key
OPENAI_API_KEY=tu-clave-openai-aqui
```

### 3. Ejecutar el Microservicio
```bash
python run.py
```

El servidor estará en: **http://localhost:8000**

## 🔌 Integración con Frontend

### Ejemplo JavaScript/TypeScript

```javascript
const API_URL = 'http://localhost:8000';

// Chat con streaming
async function chatStream(question, conversationId) {
    const response = await fetch(`${API_URL}/coach/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question: question,
            conversation_id: conversationId || `user-${Date.now()}`
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        // Procesar chunk...
    }
}

// Plan de coaching
async function getCoachPlan(userProfile, riskScore, topDrivers) {
    const response = await fetch(`${API_URL}/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_profile: userProfile,
            risk_score: riskScore,
            top_drivers: topDrivers
        })
    });
    
    return await response.json();
}
```

## 🔗 Integración con Otros Microservicios

### Ejemplo Python

```python
import requests

MICROSERVICE_URL = "http://localhost:8000"

# Llamar al microservicio desde otro servicio
def get_chat_response(question, conversation_id=None):
    response = requests.post(
        f"{MICROSERVICE_URL}/coach/stream",
        json={
            "question": question,
            "conversation_id": conversation_id
        },
        stream=True
    )
    return response

# Obtener plan de coaching
def get_coach_plan(user_profile, risk_score, top_drivers):
    response = requests.post(
        f"{MICROSERVICE_URL}/coach",
        json={
            "user_profile": user_profile,
            "risk_score": risk_score,
            "top_drivers": top_drivers
        }
    )
    return response.json()
```

### Ejemplo Node.js

```javascript
const axios = require('axios');

const MICROSERVICE_URL = 'http://localhost:8000';

// Chat con streaming
async function chatStream(question, conversationId) {
    const response = await axios.post(
        `${MICROSERVICE_URL}/coach/stream`,
        {
            question: question,
            conversation_id: conversationId
        },
        { responseType: 'stream' }
    );
    
    return response.data;
}

// Plan de coaching
async function getCoachPlan(userProfile, riskScore, topDrivers) {
    const response = await axios.post(`${MICROSERVICE_URL}/coach`, {
        user_profile: userProfile,
        risk_score: riskScore,
        top_drivers: topDrivers
    });
    
    return response.data;
}
```

## 📁 Estructura de Archivos

```
Microservicio_Openai/
├── app/                      # Código fuente del microservicio
│   ├── __init__.py
│   ├── main.py              # Endpoints FastAPI
│   ├── config.py            # Configuración
│   ├── models.py            # Modelos de datos
│   ├── rag_service.py       # Servicio RAG
│   ├── chat_service.py      # Servicio de chat
│   ├── document_processor.py # Procesador de documentos
│   └── guardrails.py        # Guardrails médicos
├── kb/                      # Documentos de conocimiento (crear manualmente)
├── requirements.txt         # Dependencias Python
├── run.py                   # Script de inicio
├── env.example              # Ejemplo de configuración
├── README.md                # Documentación principal
├── INSTRUCCIONES.md         # Este archivo
└── .gitignore               # Archivos a ignorar en Git
```

## 🔧 Configuración Avanzada

### Cambiar Puerto

Edita `.env`:
```env
SERVICE_PORT=8080  # Cambiar puerto
```

### Cambiar Modelo de OpenAI

Edita `.env`:
```env
OPENAI_MODEL=gpt-4  # Usar GPT-4 en lugar de GPT-3.5
```

### Desactivar Guardrails

Edita `.env`:
```env
ENABLE_MEDICAL_GUARDRAILS=false
```

## 📝 Cargar Documentos

1. Coloca tus documentos en la carpeta `kb/`
2. Soporta formatos: `.txt`, `.svg`
3. Recarga documentos:
   ```bash
   # Vía API
   POST http://localhost:8000/documents/reload
   
   # O sube nuevos documentos
   POST http://localhost:8000/documents/upload
   ```

## 🚀 Despliegue

### Desarrollo Local
```bash
python run.py
```

### Producción (con Uvicorn)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker (futuro)
```dockerfile
# Dockerfile puede agregarse después
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

## 🔍 Verificación

### Health Check
```bash
curl http://localhost:8000/health
```

### Documentación Interactiva
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## ⚠️ Notas Importantes

1. **API Key**: Es obligatoria para que funcione
2. **CORS**: Está configurado para aceptar cualquier origen (cambiar en producción)
3. **Memoria**: Se mantiene por `conversation_id`, se pierde al reiniciar
4. **Vector Store**: Se crea automáticamente en `chroma_db/`
5. **Documentos**: Colócalos en `kb/` antes de iniciar

## 🆘 Troubleshooting

### Error: "No module named 'app'"
- Asegúrate de estar en el directorio `Microservicio_Openai`
- Verifica que `app/__init__.py` existe

### Error: "OPENAI_API_KEY not found"
- Crea el archivo `.env` desde `env.example`
- Agrega tu API key de OpenAI

### Error: "Service not ready"
- Espera unos segundos después de iniciar
- Verifica que los documentos estén en `kb/`

---

**Listo para integrar! 🚀**


