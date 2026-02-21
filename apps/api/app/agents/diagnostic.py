"""
Diagnostic Agent: Generates the final clinical assessment.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.agents.state import ConversationState
from app.models.clinical import ClinicalAssessment
import json

DIAGNOSTIC_SYSTEM_PROMPT = """Sos un asistente clínico experto para profesionales de la salud.

IMPORTANTE:
- NO reemplazás el juicio médico profesional
- Tu análisis es de APOYO a la decisión clínica
- No das órdenes finales de tratamiento

TU TAREA:
Generar un análisis estructurado completo basado en la información recopilada.

ENFOQUE:
1. Analizar todos los síntomas, antecedentes e imágenes
2. Para cada diagnóstico diferencial, proporcionar información completa:
   - Causas generales (etiología médica estándar de la condición)
   - Factores específicos identificados en este paciente (ej: edad, comorbilidades, exposiciones)
   - Factores de riesgo presentes en este caso
   - Hallazgos clínicos que APOYAN este diagnóstico
   - Hallazgos clínicos que CONTRADICEN o hacen menos probable este diagnóstico
   - Pronóstico esperado si se confirma
   - Complicaciones potenciales si no se trata
   - Exámenes diagnósticos y pruebas necesarias para confirmar
   - Resumen de opciones de tratamiento disponibles
3. Generar diagnósticos diferenciales priorizados
4. Identificar red flags y urgencias
5. Sugerir plan de acción y estudios adicionales
6. Documentar en formato SOAP

REGLAS DE SALIDA:
- Respondé SOLO con JSON válido (sin markdown, sin texto extra)
- Ajustate exactamente al esquema pedido
- Likelihood 0-100 es heurístico, NO probabilidad real
- Sé explícito sobre limitaciones y necesidad de evaluación profesional
- Completá TODOS los campos del esquema con información relevante y específica
"""

def build_diagnostic_prompt(state: ConversationState) -> str:
    """Build the prompt for diagnostic generation"""
    
    # Extract patient data
    patient_info = state["patient_info"]
    symptoms = state["symptoms"]
    messages = state["messages"]
    images = state["images"]
    
    # Build conversation summary
    conversation_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in messages
    ])
    
    # Build image analysis summary
    image_summaries = []
    for img in images:
        analysis = img.get("analysis", {})
        image_summaries.append(
            f"- {analysis.get('description', 'No description')}\n"
            f"  Hallazgos: {', '.join(analysis.get('findings', []))}"
        )
    
    prompt = f"""INFORMACIÓN DEL PACIENTE:
{json.dumps(patient_info, indent=2, ensure_ascii=False)}

SÍNTOMAS IDENTIFICADOS:
{', '.join(symptoms)}

CONVERSACIÓN COMPLETA:
{conversation_text}
"""
    
    if image_summaries:
        prompt += f"\n\nANÁLISIS DE IMÁGENES:\n" + "\n".join(image_summaries)
    
    prompt += """

Generá un objeto JSON que matchee este esquema (respetar claves exactamente y completar TODOS los campos):
{
  "differentials": [
    {
      "name": "...",
      "likelihood": 0-100,
      "reasoning": "...",
      "urgency": "immediate|urgent|routine",
      "general_causes": ["causa médica 1", "causa médica 2", "etiología general..."],
      "patient_specific_factors": ["factor específico del paciente como edad/comorbilidades/exposiciones..."],
      "risk_factors": ["factor de riesgo identificado 1", "factor de riesgo 2..."],
      "supporting_findings": ["hallazgo que apoya este dx", "síntoma consistente con..."],
      "contradicting_findings": ["hallazgo que contradice", "ausencia de síntoma esperado..."],
      "prognosis": "descripción del pronóstico esperado si se confirma esta condición...",
      "complications": ["complicación potencial 1 si no se trata", "complicación 2..."],
      "recommended_tests": ["examen de laboratorio específico", "estudio de imagen", "prueba diagnóstica..."],
      "treatment_summary": "resumen de las opciones terapéuticas disponibles (farmacológicas, procedimientos, etc)..."
    }
  ],
  "red_flags": [{"severity":"critical|warning|info","message":"...","why_it_matters":"..."}],
  "missing_questions": ["preguntas que quedaron sin responder..."],
  "action_plan": [{"priority":"immediate|urgent|routine","action":"...","rationale":"..."}],
  "soap": {"subjective":"...","objective":"...","assessment":"...","plan":"..."},
  "patient_summary": "resumen ejecutivo del caso...",
  "limitations": "limitaciones de este análisis..."
}

IMPORTANTE: 
- Completá TODOS los campos con información específica y relevante al caso
- Incluí disclaimers apropiados y sé explícito sobre la necesidad de evaluación médica presencial
- Los arrays deben tener al menos 1-3 elementos con información útil
- Sé específico y detallado en cada campo
"""
    
    return prompt

class DiagnosticAgent:
    """Agent responsible for generating the final diagnostic assessment"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_TEXT,
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )
    
    async def run(self, state: ConversationState, progress_callback=None) -> Dict[str, Any]:
        """
        Generate the final clinical assessment.
        
        Args:
            state: Current conversation state
            progress_callback: Optional callback to report progress updates (deprecated, use SSE instead)
        
        Returns:
            Updated state with final_assessment
        """
        # Build the prompt
        user_prompt = build_diagnostic_prompt(state)
        
        messages = [
            SystemMessage(content=DIAGNOSTIC_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
        # Generate assessment
        response = await self.llm.ainvoke(messages)
        raw_json = response.content
        
        # Parse and validate
        try:
            assessment_dict = json.loads(raw_json)
            assessment = ClinicalAssessment.model_validate(assessment_dict)
        except (json.JSONDecodeError, Exception) as e:
            # Retry with repair prompt
            assessment = await self._repair_and_parse(messages, raw_json)
        
        # Convert assessment to dict
        assessment_dict = assessment.model_dump()
        
        # Create final message
        final_message = self._create_final_message(assessment)
        
        new_messages = state["messages"].copy()
        new_messages.append({
            "role": "assistant",
            "content": final_message
        })
        
        return {
            "final_assessment": assessment_dict,
            "messages": new_messages,
            "ready_for_diagnosis": True,
            "last_agent": "diagnostic",
        }
    
    async def _repair_and_parse(self, original_messages: list, raw_json: str) -> ClinicalAssessment:
        """Try to repair malformed JSON"""
        repair_prompt = HumanMessage(
            content=f"El output anterior no es JSON válido o no matchea el esquema.\n\n"
                    f"Output recibido:\n{raw_json}\n\n"
                    f"Devolvé SOLO JSON válido acorde al esquema. Sin markdown, sin explicaciones."
        )
        
        messages = original_messages + [
            HumanMessage(content=raw_json),
            repair_prompt
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            assessment_dict = json.loads(response.content)
            return ClinicalAssessment.model_validate(assessment_dict)
        except Exception as e:
            # If still failing, return a minimal valid assessment
            return self._create_fallback_assessment(str(e))
    
    def _create_fallback_assessment(self, error_msg: str) -> ClinicalAssessment:
        """Create a minimal fallback assessment when parsing fails"""
        return ClinicalAssessment(
            differentials=[{
                "name": "Evaluación incompleta",
                "likelihood": 0,
                "reasoning": "Error al generar diagnóstico estructurado",
                "urgency": "urgent"
            }],
            red_flags=[{
                "severity": "warning",
                "message": "No se pudo generar análisis completo",
                "why_it_matters": "Se requiere revisión manual del caso"
            }],
            missing_questions=["Evaluación completa pendiente"],
            action_plan=[{
                "priority": "immediate",
                "action": "Revisar caso manualmente",
                "rationale": "Error en generación automática"
            }],
            soap={
                "subjective": "Ver conversación completa",
                "objective": "Ver conversación completa",
                "assessment": f"Error: {error_msg}",
                "plan": "Revisión manual requerida"
            },
            patient_summary="Error al procesar caso - revisión manual necesaria",
            limitations=f"Error técnico en el análisis: {error_msg}"
        )
    
    def _create_final_message(self, assessment: ClinicalAssessment) -> str:
        """Create a natural language summary of the assessment"""
        msg_parts = [
            "📋 **ANÁLISIS CLÍNICO COMPLETO**\n",
            f"**Resumen:** {assessment.patient_summary}\n",
            "\n**Diagnósticos Diferenciales:**"
        ]
        
        for i, dx in enumerate(assessment.differentials[:3], 1):
            msg_parts.append(
                f"{i}. {dx.name} (probabilidad: {dx.likelihood}%, urgencia: {dx.urgency})"
            )
            msg_parts.append(f"   Razonamiento: {dx.reasoning}")
        
        if assessment.red_flags:
            msg_parts.append("\n⚠️ **Señales de Alarma:**")
            for flag in assessment.red_flags:
                msg_parts.append(f"- [{flag.severity.upper()}] {flag.message}")
        
        msg_parts.append(f"\n**Plan de Acción:**")
        for action in assessment.action_plan[:3]:
            msg_parts.append(f"- [{action.priority.upper()}] {action.action}")
        
        msg_parts.append(f"\n⚕️ **IMPORTANTE:** {assessment.limitations}")
        
        return "\n".join(msg_parts)


# Singleton instance
diagnostic_agent = DiagnosticAgent()
