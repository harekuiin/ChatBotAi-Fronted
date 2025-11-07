# -*- coding: utf-8 -*-
"""Servicio RAG - Lógica principal del sistema RAG"""

import os
from typing import List, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from pathlib import Path

from .config import settings
from .document_processor import DocumentProcessor
from .database import mongodb_service


class RAGService:
    """Servicio para manejar la lógica RAG"""
    
    def __init__(self):
        self.llm: Optional[ChatOpenAI] = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.vectordb: Optional[Chroma] = None
        self.retriever = None
        self.rag_chain = None
        self.prompt: Optional[PromptTemplate] = None
        self._initialized = False
    
    def initialize(self):
        """Inicializa el servicio RAG con todos sus componentes"""
        if self._initialized:
            return
        
        # Verificar API key
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY no está configurada. Por favor, configúrala en las variables de entorno.")
        
        os.environ['OPENAI_API_KEY'] = settings.openai_api_key
        
        # Inicializar LLM
        self.llm = ChatOpenAI(model=settings.openai_model)
        
        # Inicializar embeddings
        self.embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        
        # Definir prompt template
        template = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
Question: {question}
Context: {context}
Answer:"""
        self.prompt = PromptTemplate.from_template(template)
        
        # Cargar o crear vector store
        self._setup_vector_store()
        
        # Crear retriever
        self.retriever = self.vectordb.as_retriever()
        
        # Construir RAG chain
        self.rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        self._initialized = True
    
    def _setup_vector_store(self):
        """Configura el vector store, cargándolo si existe o creándolo si no"""
        # Verificar si el vector store ya existe
        if os.path.exists(settings.persist_directory) and os.listdir(settings.persist_directory):
            # Cargar vector store existente
            self.vectordb = Chroma(
                persist_directory=settings.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            # Crear nuevo vector store desde documentos
            documents = self._load_and_split_documents()
            self.vectordb = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=settings.persist_directory
            )
    
    def _load_and_split_documents(self) -> List[Document]:
        """Carga y divide los documentos en chunks"""
        documents_content = []
        
        # Prioridad 0: cargar documentos almacenados en MongoDB
        mongo_documents = mongodb_service.get_all_knowledge_documents()
        for entry in mongo_documents:
            content = entry.get("content", "")
            if content and content.strip():
                documents_content.append(content)

        # Cargar desde directorio de documentos si existe
        if os.path.exists(settings.documents_directory) and os.path.isdir(settings.documents_directory):
            # Buscar archivos soportados en el directorio
            supported_extensions = DocumentProcessor.get_supported_extensions()
            for file_path in Path(settings.documents_directory).rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    try:
                        content = DocumentProcessor.process_file(str(file_path))
                        if content.strip():
                            documents_content.append(content)
                    except Exception as e:
                        print(f"Error al procesar {file_path}: {str(e)}")
        
        # Si no hay documentos en el directorio, usar el archivo individual
        if not documents_content:
            if not os.path.exists(settings.document_path):
                # Crear documento de ejemplo si no existe
                self._create_sample_document()
            
            # Procesar el archivo (puede ser SVG o TXT)
            raw_document_content = DocumentProcessor.process_file(settings.document_path)
            documents_content.append(raw_document_content)
        
        # Combinar todo el contenido
        all_content = "\n\n".join(documents_content)
        
        # Dividir en chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        documents = text_splitter.create_documents([all_content])
        return documents
    
    def _create_sample_document(self):
        """Crea un documento de ejemplo si no existe"""
        sample_content = """
El sistema de Recuperación y Generación (RAG) combina las fortalezas de los modelos de recuperación de información y los modelos generativos. Su objetivo principal es mejorar la calidad y la relevancia de las respuestas generadas por los LLM, al proporcionarles información contextualizada y actualizada. Esto es crucial para reducir las "alucinaciones" de los modelos y asegurar que las respuestas sean fácticas.

En un flujo de trabajo RAG típico, cuando un usuario hace una pregunta, primero se utiliza un mecanismo de recuperación para buscar documentos relevantes en una gran base de conocimientos. Estos documentos recuperados se pasan luego a un modelo generativo (como un LLM) junto con la pregunta original. El LLM utiliza esta información contextual para formular una respuesta informada y coherente.

Este enfoque permite que los LLM accedan a información que no estaba presente en sus datos de entrenamiento, o que ha sido actualizada después de su última fecha de corte. Es particularmente útil para aplicaciones que requieren acceso a información propietaria, bases de datos internas o el conocimiento más reciente sobre un tema específico.
"""
        os.makedirs(os.path.dirname(settings.document_path) if os.path.dirname(settings.document_path) else ".", exist_ok=True)
        with open(settings.document_path, "w", encoding="utf-8") as f:
            f.write(sample_content)
    
    def ask(self, question: str) -> str:
        """Procesa una pregunta y devuelve una respuesta usando RAG"""
        if not self._initialized:
            self.initialize()
        
        if not self.rag_chain:
            raise RuntimeError("RAG chain no está inicializado")
        
        response = self.rag_chain.invoke(question)
        return response
    
    def is_ready(self) -> bool:
        """Verifica si el servicio está listo para usar"""
        return self._initialized and self.rag_chain is not None
    
    def reload_documents(self):
        """Recarga los documentos y reconstruye el vector store"""
        try:
            # Cargar nuevos documentos
            documents = self._load_and_split_documents()
            
            # Recrear vector store
            if os.path.exists(settings.persist_directory):
                import shutil
                shutil.rmtree(settings.persist_directory)
            
            self.vectordb = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=settings.persist_directory
            )
            
            # Recrear retriever
            self.retriever = self.vectordb.as_retriever()
            
            # Reconstruir RAG chain
            self.rag_chain = (
                {"context": self.retriever, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
            
            return True
        except Exception as e:
            raise RuntimeError(f"Error al recargar documentos: {str(e)}")


# Instancia global del servicio
rag_service = RAGService()
