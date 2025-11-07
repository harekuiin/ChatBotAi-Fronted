# -*- coding: utf-8 -*-
"""Configuración del backend RAG"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-0125")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # RAG Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    persist_directory: str = os.getenv("PERSIST_DIRECTORY", "./chroma_db")
    document_path: str = os.getenv("DOCUMENT_PATH", "sample_document.txt")
    documents_directory: str = os.getenv("DOCUMENTS_DIRECTORY", "./documents")
    
    # Microservice Configuration
    service_name: str = os.getenv("SERVICE_NAME", "rag-chat-service")
    service_port: int = int(os.getenv("SERVICE_PORT", "8000"))
    service_host: str = os.getenv("SERVICE_HOST", "0.0.0.0")
    reload: bool = os.getenv("RELOAD", "false").lower() == "true"
    
    # API Configuration
    api_title: str = "Chat Asistente RAG API"
    api_version: str = "1.0.0"
    api_description: str = "API para chat asistente con RAG, streaming y memoria conversacional"
    
    # Knowledge Base
    kb_directory: str = os.getenv("KB_DIRECTORY", "./kb")
    
    # MongoDB Configuration
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database_name: str = os.getenv("MONGODB_DATABASE_NAME", "hackathon_salud")
    mongodb_collection_conversations: str = os.getenv("MONGODB_COLLECTION_CONVERSATIONS", "conversations")
    mongodb_collection_knowledge: str = os.getenv("MONGODB_COLLECTION_KNOWLEDGE", "knowledge_base")
    
    # Guardrails Configuration (configurable por compañera)
    enable_medical_guardrails: bool = os.getenv("ENABLE_MEDICAL_GUARDRAILS", "true").lower() == "true"
    high_risk_threshold: float = float(os.getenv("HIGH_RISK_THRESHOLD", "0.6"))
    critical_risk_threshold: float = float(os.getenv("CRITICAL_RISK_THRESHOLD", "0.8"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

