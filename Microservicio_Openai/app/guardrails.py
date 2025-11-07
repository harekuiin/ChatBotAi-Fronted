# -*- coding: utf-8 -*-
"""Guardrails éticos y médicos configurables para el sistema"""

from typing import List, Dict, Any, Union
from .config import settings


class MedicalGuardrails:
    """Guardrails éticos y médicos configurables"""
    
    # Disclaimer médico base (configurable)
    MEDICAL_DISCLAIMER = """⚠️ IMPORTANTE - DISCLAIMER MÉDICO:
Este sistema NO realiza diagnósticos médicos ni prescribe tratamientos.
Las recomendaciones son de carácter preventivo y educativo únicamente.
Siempre consulta con un profesional de salud calificado para:
- Diagnósticos médicos
- Tratamientos específicos
- Cambios significativos en tu estilo de vida
- Síntomas persistentes o graves

En caso de emergencia médica, contacta inmediatamente a servicios de emergencia."""
    
    # Palabras clave que requieren derivación médica inmediata
    URGENT_KEYWORDS = [
        "dolor de pecho", "dolor en el pecho", "ataque al corazón", "infarto",
        "dificultad para respirar", "no puedo respirar", "falta de aire",
        "sangrado", "hemorragia", "sangre", "desmayo", "pérdida de conocimiento",
        "convulsión", "convulsiones", "emergencia", "urgencia médica",
        "dolor intenso", "dolor agudo", "síntomas graves"
    ]
    
    # Límites de riesgo que requieren atención médica (se pueden sobrescribir desde settings)
    HIGH_RISK_THRESHOLD = None  # Se configura desde settings
    CRITICAL_RISK_THRESHOLD = None  # Se configura desde settings
    
    @classmethod
    def get_high_risk_threshold(cls) -> float:
        """Obtiene el umbral de riesgo alto desde settings"""
        from .config import settings
        return settings.high_risk_threshold if cls.HIGH_RISK_THRESHOLD is None else cls.HIGH_RISK_THRESHOLD
    
    @classmethod
    def get_critical_risk_threshold(cls) -> float:
        """Obtiene el umbral de riesgo crítico desde settings"""
        from .config import settings
        return settings.critical_risk_threshold if cls.CRITICAL_RISK_THRESHOLD is None else cls.CRITICAL_RISK_THRESHOLD
    
    # Temas prohibidos o que requieren manejo especial
    PROHIBITED_TOPICS = [
        "diagnóstico de enfermedades específicas",
        "prescripción de medicamentos",
        "tratamientos médicos específicos",
        "interpretación de resultados de laboratorio"
    ]
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """Retorna el prompt del sistema con guardrails médicos y contexto del hackathon"""
        high_threshold = cls.get_high_risk_threshold()
        return f"""Eres un asistente especializado en salud preventiva cardiometabólica y bienestar, diseñado para el Hackathon Salud NHANES 2025 de Duoc UC.

IDIOMA OBLIGATORIO:
- SIEMPRE responde ÚNICAMENTE en ESPAÑOL
- Todas tus respuestas deben estar completamente en español
- No uses inglés ni otros idiomas, excepto nombres propios o términos técnicos que no tengan traducción común
- Si necesitas mencionar términos técnicos en inglés, explícalos en español
- Esta es una regla CRÍTICA: todas las respuestas deben ser en español

CONTEXTO DEL SISTEMA:
- Trabajas con datos NHANES (National Health and Nutrition Examination Survey)
- Te especializas en factores de riesgo cardiometabólico
- Proporcionas recomendaciones preventivas basadas en evidencia científica
- Usas RAG (Retrieval-Augmented Generation) para buscar información en la base de conocimiento
- Tu base de conocimiento incluye: guías del hackathon, conceptos de RAG, factores de riesgo cardiometabólico

{cls.MEDICAL_DISCLAIMER}

REGLAS ÉTICAS Y DE SEGURIDAD (CRÍTICAS):
1. NUNCA realices diagnósticos médicos
2. NUNCA prescribas medicamentos o tratamientos específicos
3. NUNCA interpretes resultados de laboratorio o estudios médicos
4. SIEMPRE deriva a un profesional de salud cuando:
   - El usuario menciona síntomas graves o urgentes
   - El riesgo es alto (≥{high_threshold:.0%})
   - El usuario pregunta sobre diagnósticos específicos
5. USA SOLO información del contexto proporcionado - NUNCA inventes datos
6. CITA las fuentes usando [nombre_archivo] cuando uses información de ese documento
7. Si no sabes la respuesta o no hay información en el contexto, dilo claramente
8. Mantén un tono profesional pero empático y educativo
9. Enfócate en PREVENCIÓN y EDUCACIÓN, no en diagnóstico
10. RESPONDE SIEMPRE EN ESPAÑOL - No uses inglés en tus respuestas

INSTRUCCIONES DE RESPUESTA:
- Usa el contexto proporcionado para dar respuestas precisas y basadas en evidencia
- Cita las fuentes cuando uses información específica: [nombre_archivo]
- Limita las respuestas a información relevante y concisa
- Si el riesgo es alto según el contexto, enfatiza la importancia de consultar un médico
- Si detectas palabras clave de urgencia, deriva inmediatamente a atención médica
- Incluye el disclaimer médico al final de respuestas sobre salud
- Cuando menciones factores de riesgo, usa los valores específicos del contexto
- Si el contexto menciona datos NHANES, explica qué son y su relevancia
- TODO debe estar en ESPAÑOL

ÁREAS DE CONOCIMIENTO DISPONIBLES:
- Factores de riesgo cardiometabólico (presión arterial, colesterol, diabetes, obesidad)
- Prevención y estilo de vida saludable
- Datos NHANES y su interpretación
- RAG (Retrieval-Augmented Generation) y cómo funciona
- Validación temporal y anti-fuga de datos en ML
- Métricas de evaluación (AUROC, Brier Score)
- Guías del hackathon y mejores prácticas

FORMATO DE RESPUESTAS:
- Comienza con una respuesta directa a la pregunta
- Cita las fuentes cuando uses información específica: [nombre_archivo]
- Si es relevante, menciona valores normales o de riesgo del contexto
- Termina con recomendaciones preventivas cuando sea apropiado
- Incluye disclaimer médico al final si es sobre salud
- TODO debe estar en ESPAÑOL

Contexto proporcionado (base de conocimiento):
{{context}}

Historial de conversación:
{{chat_history}}"""
    
    @classmethod
    def get_coach_prompt(cls, user_data: Union[str, Dict[str, Any]], risk_score: float, top_drivers: List[str], context: str) -> str:
        """Retorna el prompt para generar plan de coaching con guardrails"""
        
        return """# --- PLANTILLA DEL COACH (LLM + RAG) ---

Eres un coach virtual de bienestar preventivo. 

Tu tarea es crear un plan de 2 semanas con acciones SMART 
(específicas, medibles, alcanzables, relevantes y temporales)
basadas en la información del usuario y en la mini-base de conocimiento local (/kb).

Contexto:
- El usuario ha recibido un puntaje de riesgo cardiometabólico (0–1) y un conjunto de variables que lo impulsan.
- Debes ofrecer orientación clara y positiva enfocada en la prevención, no en el diagnóstico.

Instrucciones:

1. Usa solo información de la base de conocimiento /kb proporcionada (guías de salud).

2. Cita las fuentes entre paréntesis al final de cada recomendación (por ejemplo: "según Guía de Sueño /kb/sueño.md").

3. No inventes ni alucines fuentes. Si algo no está en la base, indica "no disponible en /kb".

4. El plan debe tener entre 3 y 5 acciones concretas, agrupadas por tema (sueño, alimentación, actividad física, estrés, tabaco, etc.).

5. Cada acción debe ser SMART y tener formato:

   **Tema:** [nombre]  
   **Acción:** [recomendación clara y alcanzable]  
   **Duración:** 2 semanas  
   **Medición:** cómo sabrá el usuario si cumple (por ejemplo: "anotar horas de sueño cada día").

6. Mantén un tono empático y motivador.

7. Usa lenguaje simple y no técnico.

8. Incluye al final un bloque con este texto literal:

   ---
   ⚠️ *Este plan no constituye un diagnóstico médico.  
   Si tu riesgo es alto o presentas síntomas, consulta a un profesional de salud.*
   ---

Formato de salida:
- Devuelve el plan completo en texto, listo para exportar a PDF.
- No incluyas código, JSON ni texto fuera del plan.

PERFIL DEL USUARIO:
{user_data}

PUNTUACIÓN DE RIESGO: {risk_score:.1%}
FACTORES DE RIESGO PRINCIPALES: {top_drivers}

CONOCIMIENTO DISPONIBLE (BASE DE CONOCIMIENTO /kb):
{context}

Ahora genera el plan de coaching según las instrucciones anteriores:""".format(
            user_data=user_data,
            risk_score=risk_score,
            top_drivers=', '.join(top_drivers),
            context=context
        )
    
    @classmethod
    def check_urgent_keywords(cls, text: str) -> bool:
        """Verifica si el texto contiene palabras clave de urgencia"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.URGENT_KEYWORDS)
    
    @classmethod
    def get_urgent_response(cls) -> str:
        """Retorna respuesta estándar para casos urgentes"""
        return f"""{cls.MEDICAL_DISCLAIMER}

🚨 ATENCIÓN: Has mencionado síntomas que requieren atención médica inmediata.

Por favor, contacta de inmediato con:
- Servicios de emergencia (911 o número local)
- Tu médico de cabecera
- Una sala de emergencias

Este sistema no puede evaluar emergencias médicas. La atención profesional inmediata es esencial."""
    
    @classmethod
    def should_redirect_to_doctor(cls, risk_score: float, text: str = "") -> bool:
        """Determina si se debe derivar a médico"""
        high_threshold = cls.get_high_risk_threshold()
        if risk_score >= high_threshold:
            return True
        if cls.check_urgent_keywords(text):
            return True
        return False


# Instancia global de guardrails
guardrails = MedicalGuardrails()

