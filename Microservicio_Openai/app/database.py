# -*- coding: utf-8 -*-
"""Módulo de base de datos MongoDB para almacenar conversaciones"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from .config import settings

logger = logging.getLogger(__name__)


class MongoDBService:
    """Servicio para interactuar con MongoDB"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.conversations_collection = None
        self._connected = False
    
    def connect(self):
        """Conecta a MongoDB"""
        try:
            self.client = MongoClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000  # 5 segundos timeout
            )
            # Verificar conexión
            self.client.admin.command('ping')
            self.db = self.client[settings.mongodb_database_name]
            self.conversations_collection = self.db[settings.mongodb_collection_conversations]
            self._connected = True
            logger.info(f"✅ Conectado a MongoDB: {settings.mongodb_database_name}")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"⚠️ No se pudo conectar a MongoDB: {str(e)}")
            logger.warning("⚠️ El sistema funcionará sin persistencia de conversaciones")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Error al conectar a MongoDB: {str(e)}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Verifica si está conectado a MongoDB"""
        if not self._connected:
            return False
        try:
            # Verificar conexión activa
            self.client.admin.command('ping')
            return True
        except Exception:
            self._connected = False
            return False
    
    def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Guarda un mensaje en la conversación
        
        Args:
            conversation_id: ID único de la conversación
            role: 'user' o 'assistant'
            content: Contenido del mensaje
            metadata: Metadatos adicionales opcionales
        
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        if not self.is_connected():
            return False
        
        try:
            message_doc = {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            self.conversations_collection.insert_one(message_doc)
            return True
        except Exception as e:
            logger.error(f"Error al guardar mensaje en MongoDB: {str(e)}")
            return False
    
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de una conversación
        
        Args:
            conversation_id: ID único de la conversación
            limit: Número máximo de mensajes a recuperar (últimos N)
        
        Returns:
            Lista de mensajes ordenados por timestamp
        """
        if not self.is_connected():
            return []
        
        try:
            messages = list(
                self.conversations_collection
                .find({"conversation_id": conversation_id})
                .sort("timestamp", 1)  # Orden ascendente (más antiguos primero)
                .limit(limit)
            )
            
            # Convertir ObjectId a string y eliminar _id
            for msg in messages:
                if "_id" in msg:
                    del msg["_id"]
                if "timestamp" in msg:
                    msg["timestamp"] = msg["timestamp"].isoformat()
            
            return messages
        except Exception as e:
            logger.error(f"Error al obtener historial de MongoDB: {str(e)}")
            return []
    
    def get_conversation_history_formatted(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> str:
        """
        Obtiene el historial formateado como string para usar en prompts
        
        Args:
            conversation_id: ID único de la conversación
            limit: Número máximo de mensajes a recuperar
        
        Returns:
            String formateado con el historial
        """
        messages = self.get_conversation_history(conversation_id, limit)
        
        if not messages:
            return "No hay historial previo de conversación."
        
        formatted_history = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                formatted_history.append(f"Usuario: {content}")
            elif role == "assistant":
                formatted_history.append(f"Asistente: {content}")
        
        return "\n".join(formatted_history)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Elimina todos los mensajes de una conversación
        
        Args:
            conversation_id: ID único de la conversación
        
        Returns:
            True si se eliminó correctamente
        """
        if not self.is_connected():
            return False
        
        try:
            result = self.conversations_collection.delete_many(
                {"conversation_id": conversation_id}
            )
            logger.info(f"Eliminados {result.deleted_count} mensajes de conversación {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar conversación de MongoDB: {str(e)}")
            return False
    
    def get_conversation_count(self, conversation_id: str) -> int:
        """
        Obtiene el número de mensajes en una conversación
        
        Args:
            conversation_id: ID único de la conversación
        
        Returns:
            Número de mensajes
        """
        if not self.is_connected():
            return 0
        
        try:
            return self.conversations_collection.count_documents(
                {"conversation_id": conversation_id}
            )
        except Exception as e:
            logger.error(f"Error al contar mensajes en MongoDB: {str(e)}")
            return 0
    
    def close(self):
        """Cierra la conexión a MongoDB"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Conexión a MongoDB cerrada")


# Instancia global del servicio MongoDB
mongodb_service = MongoDBService()

