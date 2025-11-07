# -*- coding: utf-8 -*-
"""Aplicación FastAPI principal para el backend RAG"""

from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import shutil
from pathlib import Path

from .config import settings
from .models import (
    ChatRequest, ChatResponse, HealthResponse, ErrorResponse, DocumentUploadResponse,
    CoachRequest, CoachResponse, UserProfile
)
from .rag_service import rag_service
from .chat_service import chat_service
from .document_processor import DocumentProcessor
from .database import mongodb_service
from fastapi.responses import StreamingResponse
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description
)

# Configurar CORS para permitir conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Inicializa los servicios al arrancar la aplicación"""
    try:
        # Crear directorios necesarios
        os.makedirs(settings.documents_directory, exist_ok=True)
        os.makedirs(settings.kb_directory, exist_ok=True)
        
        logger.info("Inicializando servicios...")
        
        # Inicializar MongoDB
        if mongodb_service.connect():
            logger.info("✅ MongoDB conectado correctamente")
        else:
            logger.warning("⚠️ MongoDB no disponible - el sistema funcionará sin persistencia")
        
        # Inicializar servicio de chat (principal)
        chat_service.initialize()
        logger.info("Servicio de Chat inicializado correctamente")
        
        # Inicializar servicio RAG (compatibilidad)
        rag_service.initialize()
        logger.info("Servicio RAG inicializado correctamente")
        
    except Exception as e:
        logger.error(f"Error al inicializar los servicios: {str(e)}")
        raise


@app.get("/", response_model=HealthResponse)
async def root():

    """
    ========================================
    ENDPOINT RAÍZ - Health Check Básico
    ========================================
    
    QUÉ HACE:
    - Verifica que el microservicio está funcionando
    - Endpoint más simple para probar conectividad
    - No requiere autenticación ni parámetros
    
    QUÉ RECIBE:
    - Nada (GET sin parámetros)
    
    QUÉ RETORNA:
    - JSON con status "ok" y mensaje de confirmación
    - Ejemplo: {"status": "ok", "message": "RAG Chat API está funcionando"}
    
    CÓMO USARLO:
    - GET http://localhost:8000/
    - Útil para verificar que el servidor está corriendo
    
    CASOS DE USO:
    - Health check básico del frontend
    - Verificar que el servidor responde
    - Testing de conectividad
    
    NOTAS:
    - Este endpoint siempre responde, incluso si los servicios no están listos
    - Para verificar estado completo, usa /health
    """
    return HealthResponse(
        status="ok",
        message="RAG Chat API está funcionando"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    ========================================
    ENDPOINT HEALTH CHECK - Estado Detallado
    ========================================
    
    QUÉ HACE:
    - Verifica el estado real de todos los servicios
    - Comprueba si chat_service y rag_service están listos
    - Útil para monitoreo y load balancers
    
    QUÉ RECIBE:
    - Nada (GET sin parámetros)
    
    QUÉ RETORNA:
    - Si TODO está listo: {"status": "ready", "message": "Servicios listos"}
    - Si está inicializando: {"status": "initializing", "message": "Servicios inicializando"}
    
    CÓMO USARLO:
    - GET http://localhost:8000/health
    - El frontend puede hacer polling a este endpoint para saber cuándo está listo
    
    CASOS DE USO:
    - Verificar que el microservicio está completamente operativo
    - Monitoreo de salud del servicio
    - Load balancers que verifican salud antes de enrutar tráfico
    - Frontend que espera a que el backend esté listo
    
    NOTAS:
    - Este endpoint verifica el estado REAL de los servicios
    - Si retorna "initializing", espera unos segundos y vuelve a consultar
    - Útil para implementar retry logic en el frontend
    """
    chat_ready = chat_service.is_ready()
    rag_ready = rag_service.is_ready()
    is_ready = chat_ready and rag_ready
    
    return HealthResponse(
        status="ready" if is_ready else "initializing",
        message="Servicios listos" if is_ready else "Servicios inicializando"
    )


@app.post("/coach", response_model=CoachResponse)
async def coach(request: CoachRequest):
    """
    ========================================
    ENDPOINT /coach - Plan de Coaching Personalizado
    ========================================
    
    QUÉ HACE:
    - Genera un plan de coaching personalizado de 2 semanas usando RAG
    - Busca información relevante en la base de conocimiento (/kb)
    - Aplica guardrails médicos y éticos
    - Cita las fuentes utilizadas
    
    QUÉ RECIBE (CoachRequest):
    {
        "user_profile": {
            "age": 35,                    # Edad (18-85)
            "sex": "M",                   # "M" o "F"
            "height_cm": 175.0,           # Altura en cm (120-220)
            "weight_kg": 80.0,            # Peso en kg (30-220)
            "waist_cm": 90.0,             # Cintura en cm (40-170)
            "sleep_hours": 7.0,           # Opcional: horas de sueño (3-14)
            "smokes_cig_day": 0,          # Opcional: cigarrillos/día (0-60)
            "days_mvpa_week": 3,          # Opcional: días actividad física (0-7)
            "fruit_veg_portions_day": 5.0 # Opcional: porciones fruta/verdura (0-12)
        },
        "risk_score": 0.65,               # Puntuación de riesgo (0.0 a 1.0)
        "top_drivers": [                  # Factores de riesgo principales
            "bmi",
            "waist_height_ratio",
            "sedentarismo"
        ]
    }
    
    QUÉ RETORNA (CoachResponse):
    {
        "plan": "Plan detallado de 2 semanas...\n\n⚠️ IMPORTANTE - DISCLAIMER MÉDICO...",
        "sources": ["salud_preventiva.txt", "factores_riesgo.txt"]
    }
    
    CÓMO USARLO:
    - POST http://localhost:8000/coach
    - Content-Type: application/json
    - Body: JSON con CoachRequest
    
    EJEMPLO DE REQUEST:
    ```json
    {
        "user_profile": {
            "age": 45,
            "sex": "M",
            "height_cm": 180,
            "weight_kg": 95,
            "waist_cm": 100
        },
        "risk_score": 0.72,
        "top_drivers": ["bmi", "waist_height_ratio"]
    }
    ```
    
    CASOS DE USO:
    - Frontend envía datos del usuario después de calcular riesgo
    - Generar plan personalizado basado en factores de riesgo
    - Sistema de coaching preventivo del hackathon
    
    PROCESO INTERNO:
    1. Recibe perfil de usuario, riesgo y drivers
    2. Busca en /kb documentos relevantes usando RAG (top 3)
    3. Construye contexto con fuentes citadas
    4. Genera plan con OpenAI usando el contexto
    5. Aplica guardrails médicos (disclaimer, derivación si riesgo alto)
    6. Retorna plan y lista de fuentes
    
    NOTAS IMPORTANTES:
    - Este es el endpoint PRINCIPAL del hackathon
    - Requiere que los servicios estén inicializados
    - El plan incluye disclaimer médico automático
    - Si risk_score >= HIGH_RISK_THRESHOLD, recomienda consultar médico
    - Las fuentes vienen de los documentos en /kb
    - El plan es de PREVENCIÓN, no diagnóstico médico
    """
    try:
        if not chat_service.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio de chat aún no está listo. Por favor, intenta de nuevo en unos momentos."
            )
        
        logger.info(f"Generando plan de coaching para usuario (riesgo: {request.risk_score:.1%})")
        
        # Generar plan usando el servicio de chat con RAG
        plan_data = await chat_service.generate_coach_plan(
            user_profile=request.user_profile,
            risk_score=request.risk_score,
            top_drivers=request.top_drivers
        )
        
        logger.info("Plan de coaching generado exitosamente")
        
        return CoachResponse(
            plan=plan_data["plan"],
            sources=plan_data["sources"]
        )
    
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al generar plan de coaching: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@app.post("/coach/stream")
async def coach_stream(request: ChatRequest):
    """
    ========================================
    ENDPOINT /coach/stream - Chat con Streaming
    ========================================
    
    QUÉ HACE:
    - Permite hacer preguntas al asistente con respuestas en tiempo real
    - Usa Server-Sent Events (SSE) para streaming
    - Mantiene memoria conversacional (contexto de hasta 5 mensajes)
    - Aplica guardrails médicos automáticamente
    
    QUÉ RECIBE (ChatRequest):
    {
        "question": "¿Cuáles son los factores de riesgo cardiometabólico?",
        "conversation_id": "user-123"  # Opcional: para mantener contexto
    }
    
    QUÉ RETORNA:
    - Streaming de texto en formato SSE (Server-Sent Events)
    - Cada chunk viene como: "data: texto\n\n"
    - Al finalizar envía: "data: [DONE]\n\n"
    - Content-Type: text/event-stream
    
    CÓMO USARLO EN FRONTEND:
    ```javascript
    // Opción 1: Usando fetch con streaming
    const response = await fetch('http://localhost:8000/coach/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question: "¿Qué es el RAG?",
            conversation_id: "user-123"
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        // Procesar chunk y mostrar en UI
    }
    
    // Opción 2: Usando EventSource (si fuera GET)
    // Nota: EventSource solo funciona con GET, para POST usa fetch
    ```
    
    CASOS DE USO:
    - Chat interactivo en tiempo real
    - Mejor UX: usuario ve respuesta mientras se genera
    - Conversaciones con contexto (usando conversation_id)
    - Preguntas generales sobre salud preventiva
    
    PROCESO INTERNO:
    1. Verifica guardrails (palabras clave de urgencia)
    2. Busca contexto relevante en /kb usando RAG
    3. Recupera historial de conversación (si conversation_id existe)
    4. Genera respuesta con streaming (chunk por chunk)
    5. Guarda pregunta y respuesta en memoria
    
    NOTAS IMPORTANTES:
    - Usa conversation_id para mantener contexto entre mensajes
    - Si detecta palabras de urgencia, retorna respuesta de emergencia
    - El streaming mejora la percepción de velocidad
    - La memoria se mantiene por conversation_id
    - Máximo 5 interacciones en memoria por conversación
    """
    try:
        if not chat_service.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio de chat aún no está listo."
            )
        
        conversation_id = request.conversation_id or "default"
        logger.info(f"Procesando pregunta con streaming: {request.question} (conversación: {conversation_id})")
        
        async def generate():
            async for chunk in chat_service.ask_streaming(request.question, conversation_id):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        logger.error(f"Error en streaming: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en streaming: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    ========================================
    ENDPOINT /chat - Chat Básico (Sin Memoria)
    ========================================
    
    QUÉ HACE:
    - Permite hacer preguntas al sistema RAG
    - NO mantiene memoria conversacional (cada pregunta es independiente)
    - Usa el servicio RAG básico (sin contexto de conversación)
    - Útil para preguntas aisladas
    
    QUÉ RECIBE (ChatRequest):
    {
        "question": "¿Qué es un sistema RAG?",
        "conversation_id": null  # Opcional, pero NO se usa aquí
    }
    
    QUÉ RETORNA (ChatResponse):
    {
        "answer": "Un sistema RAG es...",
        "question": "¿Qué es un sistema RAG?",
        "conversation_id": null
    }
    
    CÓMO USARLO:
    - POST http://localhost:8000/chat
    - Content-Type: application/json
    - Body: JSON con ChatRequest
    
    EJEMPLO DE REQUEST:
    ```json
    {
        "question": "¿Cuáles son los beneficios del ejercicio?",
        "conversation_id": null
    }
    ```
    
    DIFERENCIA CON /coach/stream:
    - /chat: Sin memoria, respuesta completa de una vez
    - /coach/stream: Con memoria, respuesta en streaming
    
    CASOS DE USO:
    - Preguntas aisladas sin necesidad de contexto
    - Testing del sistema RAG
    - Compatibilidad con código legacy
    - Cuando no necesitas mantener conversación
    
    NOTAS:
    - Este endpoint NO usa memoria conversacional
    - Cada pregunta es independiente
    - Más rápido que /coach/stream (no hay streaming)
    - Útil para preguntas simples y directas
    - conversation_id se ignora en este endpoint
    """
    try:
        if not rag_service.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio RAG aún no está listo. Por favor, intenta de nuevo en unos momentos."
            )
        
        logger.info(f"Procesando pregunta: {request.question}")
        
        # Procesar pregunta con RAG (sin memoria)
        answer = rag_service.ask(request.question)
        
        logger.info("Respuesta generada exitosamente")
        
        return ChatResponse(
            answer=answer,
            question=request.question,
            conversation_id=request.conversation_id
        )
    
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al procesar la pregunta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    reload_vector_store: bool = True
):
    """
    ========================================
    ENDPOINT /documents/upload - Cargar Documentos
    ========================================
    
    QUÉ HACE:
    - Permite subir documentos (SVG o TXT) a la base de conocimiento
    - Los archivos se guardan en /kb (prioridad del hackathon)
    - Opcionalmente recarga el vector store para incluir el nuevo documento
    - Valida que el archivo sea procesable
    
    QUÉ RECIBE:
    - Form-data con campo "file" (archivo SVG o TXT)
    - Query parameter opcional: "reload_vector_store" (default: true)
    
    QUÉ RETORNA (DocumentUploadResponse):
    {
        "message": "Archivo cargado exitosamente",
        "file_path": "./kb/mi_documento.txt",
        "file_type": ".txt",
        "reloaded": true  # Si se recargó el vector store
    }
    
    CÓMO USARLO:
    - POST http://localhost:8000/documents/upload
    - Content-Type: multipart/form-data
    - Body: form-data con campo "file"
    - Query: ?reload_vector_store=true (opcional)
    
    EJEMPLO CON CURL:
    ```bash
    curl -X POST "http://localhost:8000/documents/upload?reload_vector_store=true" \
         -F "file=@mi_documento.txt"
    ```
    
    EJEMPLO CON JAVASCRIPT:
    ```javascript
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    const response = await fetch('http://localhost:8000/documents/upload?reload_vector_store=true', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    console.log(result);
    ```
    
    FORMATOS SOPORTADOS:
    - .txt (archivos de texto)
    - .svg (archivos SVG con texto extraíble)
    
    PROCESO INTERNO:
    1. Valida extensión del archivo (.txt o .svg)
    2. Guarda el archivo en /kb
    3. Intenta procesar el archivo (extraer texto)
    4. Si falla, elimina el archivo y retorna error
    5. Si reload_vector_store=true, reconstruye el vector store
    6. Retorna confirmación con ruta del archivo
    
    CASOS DE USO:
    - Cargar documentos de conocimiento al sistema
    - Actualizar base de conocimiento sin reiniciar servidor
    - Agregar nuevos documentos para RAG
    - Administración de la base de conocimiento
    
    NOTAS IMPORTANTES:
    - Los archivos se guardan en /kb por defecto
    - Si reload_vector_store=false, el documento NO estará disponible hasta recargar
    - El archivo debe contener texto extraíble
    - Si el archivo es inválido, se elimina automáticamente
    - El vector store se reconstruye completamente al recargar (puede tardar)
    """
    try:
        # Verificar extensión del archivo
        file_ext = Path(file.filename).suffix.lower()
        supported_extensions = DocumentProcessor.get_supported_extensions()
        
        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de archivo no soportado. Formatos permitidos: {', '.join(supported_extensions)}"
            )
        
        # Determinar dónde guardar (prioridad: /kb)
        kb_path = Path(settings.kb_directory)
        docs_path = Path(settings.documents_directory)
        
        # Crear directorios si no existen
        os.makedirs(settings.kb_directory, exist_ok=True)
        os.makedirs(settings.documents_directory, exist_ok=True)
        
        # Guardar en /kb por defecto (base de conocimiento del hackathon)
        file_path = os.path.join(settings.kb_directory, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Archivo cargado: {file_path}")
        
        # Verificar que el archivo se puede procesar
        try:
            content = DocumentProcessor.process_file(file_path)
            if not content.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo no contiene texto extraíble"
                )
        except Exception as e:
            os.remove(file_path)  # Eliminar archivo si hay error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error al procesar el archivo: {str(e)}"
            )
        
        # Recargar vector store si se solicita
        reloaded = False
        if reload_vector_store and chat_service.is_ready():
            try:
                chat_service.reload_documents()
                rag_service.reload_documents()
                reloaded = True
                logger.info("Vector store recargado exitosamente")
            except Exception as e:
                logger.warning(f"Error al recargar vector store: {str(e)}")
        
        return DocumentUploadResponse(
            message="Archivo cargado exitosamente",
            file_path=file_path,
            file_type=file_ext,
            reloaded=reloaded
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al cargar documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar el documento: {str(e)}"
        )


@app.post("/documents/reload")
async def reload_documents():
    """
    ========================================
    ENDPOINT /documents/reload - Recargar Vector Store
    ========================================
    
    QUÉ HACE:
    - Reconstruye completamente el vector store desde cero
    - Lee todos los documentos de /kb y /documents
    - Regenera embeddings para todos los documentos
    - Actualiza el retriever con los nuevos documentos
    
    QUÉ RECIBE:
    - Nada (POST sin body)
    
    QUÉ RETORNA (HealthResponse):
    {
        "status": "ready",
        "message": "Documentos recargados y vector store reconstruido"
    }
    
    CÓMO USARLO:
    - POST http://localhost:8000/documents/reload
    - No requiere body ni parámetros
    
    EJEMPLO:
    ```bash
    curl -X POST http://localhost:8000/documents/reload
    ```
    
    CUÁNDO USARLO:
    - Después de agregar múltiples documentos sin reload automático
    - Cuando se modifican documentos existentes
    - Si el vector store parece desactualizado
    - Después de eliminar documentos manualmente
    
    PROCESO INTERNO:
    1. Elimina el vector store existente (./chroma_db)
    2. Lee todos los documentos de /kb y /documents
    3. Procesa cada documento (extrae texto de SVG si aplica)
    4. Divide en chunks según configuración
    5. Genera embeddings para cada chunk
    6. Crea nuevo vector store con todos los documentos
    7. Reconstruye los retrievers de chat_service y rag_service
    
    CASOS DE USO:
    - Actualizar base de conocimiento después de cambios masivos
    - Sincronizar vector store con archivos en disco
    - Resolver problemas de documentos no encontrados
    - Reiniciar el sistema de búsqueda
    
    NOTAS IMPORTANTES:
    - Este proceso puede tardar varios segundos/minutos según cantidad de documentos
    - Durante la recarga, el servicio puede estar temporalmente no disponible
    - Se elimina el vector store anterior (no se puede deshacer)
    - Todos los documentos deben ser válidos o fallará
    - Útil después de cargar documentos con reload_vector_store=false
    """
    try:
        if not chat_service.is_ready():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio de chat no está inicializado"
            )
        
        chat_service.reload_documents()
        rag_service.reload_documents()
        logger.info("Documentos recargados exitosamente")
        
        return HealthResponse(
            status="ready",
            message="Documentos recargados y vector store reconstruido"
        )
    
    except Exception as e:
        logger.error(f"Error al recargar documentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recargar documentos: {str(e)}"
        )


@app.get("/documents/list")
async def list_documents():
    """
    ========================================
    ENDPOINT /documents/list - Listar Documentos
    ========================================
    
    QUÉ HACE:
    - Lista todos los documentos disponibles en el sistema
    - Incluye documentos de /kb (prioridad) y /documents
    - Muestra información de cada archivo (nombre, tamaño, tipo, origen)
    
    QUÉ RECIBE:
    - Nada (GET sin parámetros)
    
    QUÉ RETORNA:
    {
        "documents": [
            {
                "name": "salud_preventiva.txt",
                "path": "./kb/salud_preventiva.txt",
                "size": 12345,  # bytes
                "type": ".txt",
                "source": "kb"  # o "documents"
            },
            ...
        ],
        "count": 5,
        "kb_directory": "./kb",
        "documents_directory": "./documents"
    }
    
    CÓMO USARLO:
    - GET http://localhost:8000/documents/list
    - No requiere parámetros
    
    EJEMPLO DE RESPUESTA:
    ```json
    {
        "documents": [
            {
                "name": "factores_riesgo.txt",
                "path": "./kb/factores_riesgo.txt",
                "size": 8567,
                "type": ".txt",
                "source": "kb"
            },
            {
                "name": "recomendaciones.svg",
                "path": "./kb/recomendaciones.svg",
                "size": 12340,
                "type": ".svg",
                "source": "kb"
            }
        ],
        "count": 2,
        "kb_directory": "./kb",
        "documents_directory": "./documents"
    }
    ```
    
    CASOS DE USO:
    - Ver qué documentos están cargados en el sistema
    - Verificar que un documento se cargó correctamente
    - Administración de la base de conocimiento
    - Debugging: ver qué documentos están disponibles para RAG
    - Frontend que muestra lista de documentos disponibles
    
    PROCESO INTERNO:
    1. Busca archivos en /kb con extensiones soportadas (.txt, .svg)
    2. Busca archivos en /documents con extensiones soportadas
    3. Para cada archivo, extrae: nombre, ruta, tamaño, tipo, origen
    4. Retorna lista completa con metadatos
    
    NOTAS IMPORTANTES:
    - Solo lista archivos con extensiones soportadas (.txt, .svg)
    - Los documentos de /kb aparecen primero (prioridad)
    - El campo "source" indica de dónde viene cada documento
    - El tamaño está en bytes
    - No verifica si los documentos están en el vector store
    - Útil para verificar estado de la base de conocimiento
    """
    try:
        documents = []
        supported_extensions = DocumentProcessor.get_supported_extensions()
        
        # Listar documentos de /kb (prioridad)
        kb_path = Path(settings.kb_directory)
        if kb_path.exists():
            for file_path in kb_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    file_size = file_path.stat().st_size
                    documents.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_size,
                        "type": file_path.suffix.lower(),
                        "source": "kb"
                    })
        
        # Listar documentos de /documents
        docs_path = Path(settings.documents_directory)
        if docs_path.exists():
            for file_path in docs_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    file_size = file_path.stat().st_size
                    documents.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_size,
                        "type": file_path.suffix.lower(),
                        "source": "documents"
                    })
        
        return {
            "documents": documents,
            "count": len(documents),
            "kb_directory": settings.kb_directory,
            "documents_directory": settings.documents_directory
        }
    
    except Exception as e:
        logger.error(f"Error al listar documentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar documentos: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Excepción no manejada: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Error interno del servidor",
            detail=str(exc)
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.reload
    )

