# -*- coding: utf-8 -*-
"""Servicio de Chat con RAG, Streaming y Memoria Conversacional"""

import os
from typing import List, Optional, AsyncIterator, Dict, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from pathlib import Path
import json

from .config import settings
from .document_processor import DocumentProcessor
from .models import UserProfile
from .guardrails import guardrails
from .database import mongodb_service
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """Servicio de chat asistente con RAG, streaming y memoria"""
    
    def __init__(self):
        self.llm: Optional[ChatOpenAI] = None
        self.llm_streaming: Optional[ChatOpenAI] = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.vectordb: Optional[Chroma] = None
        self.retriever = None
        self.rag_chain = None
        self.rag_chain_streaming = None
        self.prompt: Optional[ChatPromptTemplate] = None
        self._initialized = False
    
    def initialize(self):
        """Inicializa el servicio de chat con todos sus componentes"""
        if self._initialized:
            return
        
        # Verificar API key
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY no está configurada. Por favor, configúrala en las variables de entorno.")
        
        os.environ['OPENAI_API_KEY'] = settings.openai_api_key
        
        # Inicializar LLM (sin streaming)
        # El idioma español se controla mediante el prompt del sistema
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7
        )
        
        # Inicializar LLM (con streaming)
        # El idioma español se controla mediante el prompt del sistema
        self.llm_streaming = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            streaming=True
        )
        
        # Inicializar embeddings
        self.embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        
        # Definir prompt template con sistema de mensajes usando guardrails
        # Prompt mejorado según especificaciones del hackathon
        if settings.enable_medical_guardrails:
            system_prompt = guardrails.get_system_prompt()
        else:
            system_prompt = """Eres un asistente especializado en salud preventiva cardiometabólica y bienestar, diseñado para el Hackathon Salud NHANES 2025 de Duoc UC.

IDIOMA OBLIGATORIO:
- SIEMPRE responde ÚNICAMENTE en ESPAÑOL
- Todas tus respuestas deben estar completamente en español
- No uses inglés ni otros idiomas, excepto nombres propios o términos técnicos que no tengan traducción común
- Si necesitas mencionar términos técnicos en inglés, explícalos en español

CONTEXTO DEL SISTEMA:
- Trabajas con datos NHANES (National Health and Nutrition Examination Survey)
- Te especializas en factores de riesgo cardiometabólico
- Proporcionas recomendaciones preventivas basadas en evidencia científica
- Usas RAG (Retrieval-Augmented Generation) para buscar información en la base de conocimiento

INSTRUCCIONES CRÍTICAS:
1. USA SOLO información del contexto proporcionado - NUNCA inventes datos
2. CITA las fuentes usando [nombre_archivo] cuando uses información de ese documento
3. Si no encuentras información relevante en el contexto, dilo claramente
4. Mantén un tono profesional pero empático y educativo
5. Enfócate en PREVENCIÓN y EDUCACIÓN, no en diagnóstico
6. Limita las respuestas a información relevante y concisa
7. Cuando menciones factores de riesgo, usa los valores específicos del contexto
8. Si el contexto menciona datos NHANES, explica qué son y su relevancia
9. RESPONDE SIEMPRE EN ESPAÑOL - No uses inglés en tus respuestas

ÁREAS DE CONOCIMIENTO:
- Factores de riesgo cardiometabólico (presión arterial, colesterol, diabetes, obesidad)
- Prevención y estilo de vida saludable
- Datos NHANES y su interpretación
- RAG (Retrieval-Augmented Generation) y cómo funciona
- Validación temporal y anti-fuga de datos en ML
- Métricas de evaluación (AUROC, Brier Score)

FORMATO DE RESPUESTAS:
- Comienza con una respuesta directa a la pregunta
- Cita las fuentes cuando uses información específica: [nombre_archivo]
- Si es relevante, menciona valores normales o de riesgo del contexto
- Termina con recomendaciones preventivas cuando sea apropiado
- TODO debe estar en ESPAÑOL

Contexto proporcionado (base de conocimiento):
{context}

Historial de conversación:
{chat_history}"""
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Cargar o crear vector store
        self._setup_vector_store()
        
        # Crear retriever
        self.retriever = self.vectordb.as_retriever(
            search_kwargs={"k": 3}  # Top 3 documentos más relevantes
        )
        
        # Construir RAG chain (sin streaming)
        self.rag_chain = (
            {
                "context": lambda x: self._format_context(self.retriever.invoke(x["question"])),
                "chat_history": lambda x: self._get_chat_history(x.get("conversation_id", "default")),
                "messages": lambda x: [HumanMessage(content=x["question"])]
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Construir RAG chain (con streaming)
        self.rag_chain_streaming = (
            {
                "context": lambda x: self._format_context(self.retriever.invoke(x["question"])),
                "chat_history": lambda x: self._get_chat_history(x.get("conversation_id", "default")),
                "messages": lambda x: [HumanMessage(content=x["question"])]
            }
            | self.prompt
            | self.llm_streaming
        )
        
        self._initialized = True
    
    def _setup_vector_store(self):
        """Configura el vector store desde /kb o documentos con metadatos de fuentes"""
        # Prioridad 1: Cargar desde /kb (base de conocimiento del hackathon)
        kb_directory = Path("./kb")
        documents_directory = Path(settings.documents_directory)
        
        documents_list = []  # Lista de objetos Document con metadatos
        
        # Cargar desde /kb si existe
        if kb_directory.exists() and kb_directory.is_dir():
            supported_extensions = DocumentProcessor.get_supported_extensions()
            for file_path in kb_directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    try:
                        content = DocumentProcessor.process_file(str(file_path))
                        if content.strip():
                            # Crear documento con metadatos
                            doc = Document(
                                page_content=content,
                                metadata={
                                    "source": str(file_path),
                                    "filename": file_path.name,
                                    "file_type": file_path.suffix.lower(),
                                    "directory": "kb"
                                }
                            )
                            documents_list.append(doc)
                    except Exception as e:
                        logger.warning(f"Error al procesar {file_path}: {str(e)}")
        
        # Cargar desde documents_directory si no hay /kb
        if not documents_list and documents_directory.exists():
            supported_extensions = DocumentProcessor.get_supported_extensions()
            for file_path in documents_directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    try:
                        content = DocumentProcessor.process_file(str(file_path))
                        if content.strip():
                            # Crear documento con metadatos
                            doc = Document(
                                page_content=content,
                                metadata={
                                    "source": str(file_path),
                                    "filename": file_path.name,
                                    "file_type": file_path.suffix.lower(),
                                    "directory": "documents"
                                }
                            )
                            documents_list.append(doc)
                    except Exception as e:
                        logger.warning(f"Error al procesar {file_path}: {str(e)}")
        
        # Si no hay documentos, crear uno de ejemplo
        if not documents_list:
            sample_content = self._create_sample_kb_content()
            doc = Document(
                page_content=sample_content,
                metadata={
                    "source": "sample_kb",
                    "filename": "sample_kb.txt",
                    "file_type": ".txt",
                    "directory": "generated"
                }
            )
            documents_list.append(doc)
        
        # Dividir cada documento en chunks manteniendo metadatos
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        # Dividir cada documento manteniendo sus metadatos
        all_documents = []
        for doc in documents_list:
            chunks = text_splitter.split_documents([doc])
            all_documents.extend(chunks)
        
        # Crear o cargar vector store
        if os.path.exists(settings.persist_directory) and os.listdir(settings.persist_directory):
            self.vectordb = Chroma(
                persist_directory=settings.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            self.vectordb = Chroma.from_documents(
                documents=all_documents,
                embedding=self.embeddings,
                persist_directory=settings.persist_directory
            )
    
    def _format_context(self, docs: List[Document]) -> str:
        """Formatea los documentos recuperados con citas según especificaciones del hackathon"""
        if not docs:
            return "No se encontró información relevante en la base de conocimiento."
        
        formatted_context = []
        for i, doc in enumerate(docs, 1):
            # Priorizar filename de metadatos (más confiable)
            filename = doc.metadata.get('filename')
            
            # Si no hay filename, intentar extraer de source
            if not filename:
                source = doc.metadata.get('source', f'Documento {i}')
                if isinstance(source, str):
                    if '/' in source or '\\' in source:
                        # Es una ruta, extraer nombre de archivo
                        filename = Path(source).name
                    else:
                        filename = source
                else:
                    filename = f"fuente_{i}.txt"
            
            content = doc.page_content
            
            # Formato mejorado con nombre de archivo claro para citas
            formatted_context.append(f"=== {filename} ===\n{content}")
        
        return "\n\n".join(formatted_context)
    
    def _get_chat_history(self, conversation_id: str) -> str:
        """Obtiene el historial de conversación formateado desde MongoDB"""
        # Usar MongoDB para obtener historial
        return mongodb_service.get_conversation_history_formatted(conversation_id, limit=10)
    
    def _create_sample_kb_content(self) -> str:
        """Crea contenido de ejemplo para la base de conocimiento"""
        return """
INFORMACIÓN SOBRE SALUD PREVENTIVA Y BIENESTAR

1. FACTORES DE RIESGO CARDIOMETABÓLICO:
- Edad avanzada aumenta el riesgo
- Índice de masa corporal (BMI) elevado (>25) es un factor de riesgo
- Presión arterial alta (>130/80) aumenta el riesgo cardiovascular
- Niveles elevados de glucosa o hemoglobina A1c indican riesgo de diabetes
- Circunferencia de cintura elevada está asociada con riesgo metabólico

2. RECOMENDACIONES PREVENTIVAS:
- Mantener un peso saludable (BMI entre 18.5 y 24.9)
- Realizar actividad física regular (al menos 150 minutos semanales)
- Seguir una dieta balanceada rica en frutas y verduras
- Limitar el consumo de azúcares y grasas saturadas
- Dormir entre 7-9 horas por noche
- Evitar el tabaquismo
- Controlar el estrés

3. IMPORTANTE:
- Estas recomendaciones son de carácter preventivo y educativo
- Siempre consulta con un profesional de salud para diagnósticos
- Si experimentas síntomas graves, busca atención médica inmediata
"""
    
    def ask(self, question: str, conversation_id: str = "default") -> str:
        """Procesa una pregunta y devuelve una respuesta usando RAG"""
        if not self._initialized:
            self.initialize()
        
        if not self.rag_chain:
            raise RuntimeError("RAG chain no está inicializado")
        
        # Verificar guardrails médicos si están habilitados
        if settings.enable_medical_guardrails:
            if guardrails.check_urgent_keywords(question):
                logger.warning(f"Palabras clave de urgencia detectadas en pregunta: {question[:50]}...")
                return guardrails.get_urgent_response()
        
        # Procesar pregunta
        request_data = {
            "question": question,
            "conversation_id": conversation_id
        }
        response = self.rag_chain.invoke(request_data)
        
        # Guardar en MongoDB
        mongodb_service.save_message(conversation_id, "user", question)
        mongodb_service.save_message(conversation_id, "assistant", response)
        
        return response
    
    async def ask_streaming(self, question: str, conversation_id: str = "default") -> AsyncIterator[str]:
        """Procesa una pregunta y devuelve respuesta en streaming"""
        if not self._initialized:
            self.initialize()
        
        if not self.rag_chain_streaming:
            raise RuntimeError("RAG chain streaming no está inicializado")
        
        # Acumular respuesta completa para guardar en MongoDB
        full_response = ""
        
        # Stream de respuesta
        request_data = {
            "question": question,
            "conversation_id": conversation_id
        }
        async for chunk in self.rag_chain_streaming.astream(request_data):
            if hasattr(chunk, 'content'):
                content = chunk.content
                full_response += content
                yield content
        
        # Guardar en MongoDB después de completar
        mongodb_service.save_message(conversation_id, "user", question)
        mongodb_service.save_message(conversation_id, "assistant", full_response)
    
    def is_ready(self) -> bool:
        """Verifica si el servicio está listo para usar"""
        return self._initialized and self.rag_chain is not None
    
    def reload_documents(self):
        """Recarga los documentos y reconstruye el vector store"""
        try:
            # Limpiar vector store
            if os.path.exists(settings.persist_directory):
                import shutil
                shutil.rmtree(settings.persist_directory)
            
            # Reconstruir
            self._setup_vector_store()
            
            # Recrear retriever
            self.retriever = self.vectordb.as_retriever(search_kwargs={"k": 3})
            
            # Reconstruir chains
            self.rag_chain = (
                {
                    "context": lambda x: self._format_context(self.retriever.invoke(x["question"])),
                    "chat_history": lambda x: self._get_chat_history(x.get("conversation_id", "default")),
                    "messages": lambda x: [HumanMessage(content=x["question"])]
                }
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
            
            self.rag_chain_streaming = (
                {
                    "context": lambda x: self._format_context(self.retriever.invoke(x["question"])),
                    "chat_history": lambda x: self._get_chat_history(x.get("conversation_id", "default")),
                    "messages": lambda x: [HumanMessage(content=x["question"])]
                }
                | self.prompt
                | self.llm_streaming
            )
            
            return True
        except Exception as e:
            raise RuntimeError(f"Error al recargar documentos: {str(e)}")
    
    async def generate_coach_plan(
        self,
        user_profile: UserProfile,
        risk_score: float,
        top_drivers: List[str]
    ) -> Dict[str, Any]:
        """
        Genera plan de coaching personalizado según especificaciones del hackathon
        
        Sigue el template de guia.md:
        1. Buscar en /kb usando RAG
        2. Construir contexto con fuentes
        3. Generar plan con OpenAI (JSON)
        4. Retornar plan y sources
        """
        if not self._initialized:
            self.initialize()
        
        # 1. Buscar en KB usando RAG - buscar recomendaciones para los drivers principales
        area_riesgo = ", ".join(top_drivers[:3])  # Top 3 drivers
        search_query = f"recomendaciones para {area_riesgo} factores de riesgo salud preventiva"
        
        # Recuperar documentos relevantes
        relevant_docs = self.retriever.invoke(search_query)
        
        # 2. Construir contexto con fuentes
        context_parts = []
        sources = []
        
        for i, doc in enumerate(relevant_docs[:3], 1):  # Top 3 documentos
            source_name = doc.metadata.get('source', f'Documento {i}')
            # Extraer nombre de archivo de la ruta
            if isinstance(source_name, str):
                filename = Path(source_name).name if '/' in source_name or '\\' in source_name else source_name
            else:
                filename = f"fuente_{i}.txt"
            
            context_parts.append(f"=== {filename} ===\n{doc.page_content}")
            if filename not in sources:
                sources.append(filename)
        
        context = "\n\n".join(context_parts)
        
        # 3. Construir prompt según template del hackathon
        user_data_dict = {
            "age": user_profile.age,
            "sex": user_profile.sex,
            "height_cm": user_profile.height_cm,
            "weight_kg": user_profile.weight_kg,
            "waist_cm": user_profile.waist_cm,
            "sleep_hours": user_profile.sleep_hours,
            "smokes_cig_day": user_profile.smokes_cig_day,
            "days_mvpa_week": user_profile.days_mvpa_week,
            "fruit_veg_portions_day": user_profile.fruit_veg_portions_day
        }
        
        # Convertir a JSON string solo para el prompt
        user_data_json = json.dumps(user_data_dict, indent=2, ensure_ascii=False)
        
        # Usar guardrails para el prompt del coach
        if settings.enable_medical_guardrails:
            prompt = guardrails.get_coach_prompt(
                user_data=user_data_json,
                risk_score=risk_score,
                top_drivers=top_drivers,
                context=context
            )
        else:
            # Prompt básico sin guardrails (solo para desarrollo)
            prompt = f"""Eres un coach de bienestar preventivo. Genera un plan personalizado de 2 semanas para el usuario.

IDIOMA OBLIGATORIO:
- SIEMPRE responde ÚNICAMENTE en ESPAÑOL
- El plan completo debe estar en español
- No uses inglés ni otros idiomas

PERFIL DEL USUARIO:
{user_data_json}

PUNTUACIÓN DE RIESGO: {risk_score:.1%}
FACTORES DE RIESGO PRINCIPALES: {', '.join(top_drivers)}

CONOCIMIENTO DISPONIBLE (BASE DE CONOCIMIENTO):
{context}

REGLAS ESTRICTAS:
- USA SOLO información del contexto proporcionado
- CITA las fuentes usando [nombre_archivo] cuando uses información de ese documento
- NO inventes información que no esté en el contexto
- El plan debe ser específico, accionable y de 2 semanas
- Enfócate en los factores de riesgo principales: {', '.join(top_drivers[:3])}
- TODO el plan debe estar en ESPAÑOL

Devuelve SOLO un JSON válido con este formato:
{{
  "plan": "Plan detallado de 2 semanas aquí... (TODO EN ESPAÑOL)",
  "sources": ["archivo1.txt", "archivo2.txt"]
}}

JSON:"""
        
        # 4. Llamar a OpenAI con formato JSON
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # 5. Extraer y validar respuesta JSON
        response_text = response.choices[0].message.content.strip()
        
        try:
            plan_data = json.loads(response_text)
            
            # Validar estructura
            if "plan" not in plan_data:
                raise ValueError("La respuesta no contiene 'plan'")
            if "sources" not in plan_data:
                plan_data["sources"] = sources  # Usar fuentes recuperadas si no vienen en respuesta
            
            # Asegurar que sources es una lista
            if isinstance(plan_data["sources"], str):
                plan_data["sources"] = [plan_data["sources"]]
            
            # Combinar sources de RAG y de la respuesta
            all_sources = list(set(sources + plan_data["sources"]))
            
            return {
                "plan": plan_data["plan"],
                "sources": all_sources
            }
        
        except json.JSONDecodeError as e:
            # Si falla el parsing, crear respuesta de fallback
            logger.warning(f"Error parseando JSON de OpenAI: {str(e)}")
            return {
                "plan": f"Plan personalizado basado en tu perfil (riesgo: {risk_score:.1%}).\n\n"
                       f"Factores principales a abordar: {', '.join(top_drivers)}.\n\n"
                       f"⚠️ IMPORTANTE: Este sistema NO realiza diagnósticos médicos. "
                       f"Siempre consulta con un profesional de salud.\n\n"
                       f"Fuentes consultadas: {', '.join(sources)}",
                "sources": sources
            }


# Instancia global del servicio
chat_service = ChatService()
