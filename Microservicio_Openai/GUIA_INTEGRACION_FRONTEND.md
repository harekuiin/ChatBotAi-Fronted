# 🚀 Guía de Integración - Frontend Original

## ✅ Estado del Microservicio

El microservicio está **simplificado y listo** para integrar con tu frontend original.

### Simplificaciones Aplicadas:
- ✅ Eliminadas conversiones JSON innecesarias
- ✅ Código más limpio y directo
- ✅ Misma funcionalidad, menos complejidad
- ✅ Optimizado para mejor rendimiento

---

## 📋 Paso 1: Configurar el Microservicio

### 1.1 Instalar Dependencias
```bash
cd Microservicio_Openai
pip install -r requirements.txt
```

### 1.2 Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
copy env.example .env

# Editar .env y agregar tu API key
OPENAI_API_KEY=tu-clave-openai-aqui
```

### 1.3 Ejecutar el Microservicio
```bash
python run.py
```

El servidor estará disponible en: **http://localhost:8000**

---

## 🔌 Paso 2: Endpoints Disponibles

### Endpoints Principales para el Frontend:

#### 1. **Health Check**
```javascript
GET http://localhost:8000/health
```
Verifica que el servidor esté listo.

#### 2. **Chat con Streaming** (Recomendado)
```javascript
POST http://localhost:8000/coach/stream
Content-Type: application/json

{
  "question": "Tu pregunta aquí",
  "conversation_id": "user-123"  // Opcional
}
```
Retorna: Server-Sent Events (SSE) con respuesta en tiempo real.

#### 3. **Chat Básico** (Sin streaming)
```javascript
POST http://localhost:8000/chat
Content-Type: application/json

{
  "question": "Tu pregunta aquí",
  "conversation_id": "user-123"  // Opcional
}
```
Retorna: JSON con respuesta completa.

#### 4. **Plan de Coaching Personalizado**
```javascript
POST http://localhost:8000/coach
Content-Type: application/json

{
  "user_profile": {
    "age": 35,
    "sex": "M",
    "height_cm": 175.0,
    "weight_kg": 80.0,
    "waist_cm": 90.0,
    "sleep_hours": 7.0,
    "smokes_cig_day": 0,
    "days_mvpa_week": 3,
    "fruit_veg_portions_day": 5.0
  },
  "risk_score": 0.65,
  "top_drivers": ["bmi", "waist_height_ratio"]
}
```
Retorna: Plan personalizado de 2 semanas con fuentes.

---

## 💻 Paso 3: Ejemplos de Código para Frontend

### 3.1 Chat con Streaming (JavaScript)

```javascript
const API_URL = 'http://localhost:8000';

async function chatWithStreaming(question, conversationId = null) {
    const response = await fetch(`${API_URL}/coach/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: question,
            conversation_id: conversationId || `user-${Date.now()}`
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                    return fullResponse;
                }
                fullResponse += data;
                // Actualizar UI con cada chunk
                updateChatUI(data);
            }
        }
    }

    return fullResponse;
}

function updateChatUI(chunk) {
    // Tu lógica para actualizar la UI
    const chatContainer = document.getElementById('chat-messages');
    const lastMessage = chatContainer.lastElementChild;
    if (lastMessage && lastMessage.classList.contains('ai-message')) {
        lastMessage.textContent += chunk;
    } else {
        const newMessage = document.createElement('div');
        newMessage.className = 'ai-message';
        newMessage.textContent = chunk;
        chatContainer.appendChild(newMessage);
    }
}
```

### 3.2 Chat Básico (Sin Streaming)

```javascript
async function chatBasic(question, conversationId = null) {
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                conversation_id: conversationId || `user-${Date.now()}`
            })
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const data = await response.json();
        return data.answer;
    } catch (error) {
        console.error('Error en chat:', error);
        throw error;
    }
}
```

### 3.3 Plan de Coaching

```javascript
async function generateCoachPlan(userProfile, riskScore, topDrivers) {
    try {
        const response = await fetch(`${API_URL}/coach`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_profile: userProfile,
                risk_score: riskScore,
                top_drivers: topDrivers
            })
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const data = await response.json();
        return {
            plan: data.plan,
            sources: data.sources
        };
    } catch (error) {
        console.error('Error generando plan:', error);
        throw error;
    }
}
```

### 3.4 Verificar Estado del Servidor

```javascript
async function checkServerHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'ready') {
            console.log('✅ Servidor listo');
            return true;
        } else {
            console.log('⏳ Servidor inicializando...');
            return false;
        }
    } catch (error) {
        console.error('❌ Servidor no disponible:', error);
        return false;
    }
}
```

---

## 🔧 Paso 4: Configuración CORS

El microservicio ya tiene CORS configurado para aceptar conexiones desde cualquier origen:

```python
# Ya configurado en main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Acepta todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Nota:** En producción, cambia `allow_origins=["*"]` por los orígenes específicos de tu frontend.

---

## 📝 Paso 5: Manejo de Errores

### Ejemplo Completo con Manejo de Errores:

```javascript
async function sendMessage(question) {
    try {
        // Verificar que el servidor esté listo
        const healthCheck = await checkServerHealth();
        if (!healthCheck) {
            throw new Error('El servidor no está listo. Intenta de nuevo en unos momentos.');
        }

        // Enviar mensaje con streaming
        const response = await chatWithStreaming(question, getConversationId());
        
        return response;
    } catch (error) {
        console.error('Error:', error);
        
        // Mostrar mensaje de error al usuario
        showErrorMessage(error.message || 'Error al conectar con el servidor');
        
        // Reintentar después de 3 segundos
        setTimeout(() => {
            sendMessage(question);
        }, 3000);
    }
}
```

---

## 🎯 Paso 6: Integración Completa (Ejemplo React)

```jsx
import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000';

function ChatComponent() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId] = useState(`user-${Date.now()}`);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch(`${API_URL}/coach/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: input,
                    conversation_id: conversationId
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiMessage = { role: 'assistant', content: '' };

            setMessages(prev => [...prev, aiMessage]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            setIsLoading(false);
                            return;
                        }
                        aiMessage.content += data;
                        setMessages(prev => {
                            const newMessages = [...prev];
                            newMessages[newMessages.length - 1] = { ...aiMessage };
                            return newMessages;
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Error al conectar con el servidor'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        {msg.content}
                    </div>
                ))}
            </div>
            <div className="input-area">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Escribe tu pregunta..."
                />
                <button onClick={sendMessage} disabled={isLoading}>
                    {isLoading ? 'Enviando...' : 'Enviar'}
                </button>
            </div>
        </div>
    );
}

export default ChatComponent;
```

---

## 🔍 Paso 7: Verificar que Funciona

### 7.1 Verificar Servidor
```bash
# En otra terminal
curl http://localhost:8000/health
```

Debería retornar:
```json
{
  "status": "ready",
  "message": "Servicios listos"
}
```

### 7.2 Probar desde el Navegador
Abre la consola del navegador (F12) y ejecuta:

```javascript
fetch('http://localhost:8000/health')
    .then(r => r.json())
    .then(console.log);
```

### 7.3 Probar Chat
```javascript
fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: '¿Qué es RAG?',
        conversation_id: 'test'
    })
})
.then(r => r.json())
.then(console.log);
```

---

## 📚 Documentación Completa

Una vez que el microservicio esté corriendo, accede a:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Aquí encontrarás:
- Todos los endpoints disponibles
- Ejemplos de requests y responses
- Posibilidad de probar los endpoints directamente

---

## ⚠️ Notas Importantes

1. **Puerto:** Por defecto el microservicio corre en el puerto 8000. Si necesitas cambiarlo, edita `.env`:
   ```
   SERVICE_PORT=8000
   ```

2. **CORS:** En producción, configura los orígenes permitidos en `app/main.py`.

3. **API Key:** Asegúrate de tener tu `OPENAI_API_KEY` configurada en el archivo `.env`.

4. **Memoria Conversacional:** El `conversation_id` mantiene el contexto. Usa el mismo ID para mantener la conversación.

5. **Streaming:** El endpoint `/coach/stream` es más eficiente para respuestas largas y mejor UX.

---

## 🆘 Solución de Problemas

### El servidor no responde
- Verifica que esté corriendo: `python run.py`
- Revisa los logs en la terminal
- Verifica el puerto: `netstat -ano | findstr :8000`

### Error de CORS
- El microservicio ya tiene CORS configurado
- Si persiste, verifica que el frontend esté haciendo requests a `http://localhost:8000`

### Error de API Key
- Verifica que el archivo `.env` tenga `OPENAI_API_KEY=tu-clave`
- No debe tener espacios alrededor del `=`

---

## ✅ Checklist de Integración

- [ ] Microservicio instalado y configurado
- [ ] `.env` configurado con `OPENAI_API_KEY`
- [ ] Servidor corriendo en `http://localhost:8000`
- [ ] Health check responde correctamente
- [ ] Frontend configurado con URL correcta
- [ ] CORS funcionando (sin errores en consola)
- [ ] Chat básico funcionando
- [ ] Streaming funcionando (si lo usas)

---

**¡Listo para integrar!** 🚀

Si tienes dudas, revisa la documentación en `http://localhost:8000/docs` o consulta el archivo `README.md`.

