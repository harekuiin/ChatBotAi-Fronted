# -*- coding: utf-8 -*-
"""Modelos Pydantic para requests y responses"""

from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Request para enviar una pregunta al chat"""
    question: str = Field(..., description="Pregunta del usuario", min_length=1)
    conversation_id: Optional[str] = Field(None, description="ID de conversación (opcional)")


class ChatResponse(BaseModel):
    """Response con la respuesta del sistema RAG"""
    answer: str = Field(..., description="Respuesta generada por el sistema RAG")
    question: str = Field(..., description="Pregunta original")
    conversation_id: Optional[str] = Field(None, description="ID de conversación")


class HealthResponse(BaseModel):
    """Response para el endpoint de health check"""
    status: str = Field(..., description="Estado del servicio")
    message: str = Field(..., description="Mensaje descriptivo")


class ErrorResponse(BaseModel):
    """Response para errores"""
    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")


class DocumentUploadResponse(BaseModel):
    """Response para carga de documentos"""
    message: str = Field(..., description="Mensaje de confirmación")
    file_path: str = Field(..., description="Ruta del archivo cargado")
    file_type: str = Field(..., description="Tipo de archivo")
    reloaded: bool = Field(..., description="Si el vector store fue recargado")


# Modelos para el hackathon - Coach de Bienestar Preventivo
class UserProfile(BaseModel):
    """Perfil de usuario para el coach"""
    age: int = Field(..., ge=18, le=85, description="Edad del usuario")
    sex: str = Field(..., pattern="^[MF]$", description="Sexo: M o F")
    height_cm: float = Field(..., ge=120, le=220, description="Altura en centímetros")
    weight_kg: float = Field(..., ge=30, le=220, description="Peso en kilogramos")
    waist_cm: float = Field(..., ge=40, le=170, description="Circunferencia de cintura en cm")
    sleep_hours: Optional[float] = Field(None, ge=3, le=14, description="Horas de sueño por noche")
    smokes_cig_day: Optional[int] = Field(None, ge=0, le=60, description="Cigarrillos por día")
    days_mvpa_week: Optional[int] = Field(None, ge=0, le=7, description="Días de actividad física moderada/vigorosa por semana")
    fruit_veg_portions_day: Optional[float] = Field(None, ge=0, le=12, description="Porciones de frutas y verduras por día")


class CoachRequest(BaseModel):
    """Request para generar plan de coaching personalizado"""
    user_profile: UserProfile = Field(..., description="Perfil del usuario")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Puntuación de riesgo (0.0 a 1.0)")
    top_drivers: List[str] = Field(..., description="Lista de factores de riesgo principales")


class CoachResponse(BaseModel):
    """Response con el plan de coaching generado"""
    plan: str = Field(..., description="Plan personalizado de 2 semanas")
    sources: List[str] = Field(..., description="Lista de fuentes citadas desde /kb")

