"""
Interviewer Agent: Conducts the medical interview with the patient.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.core.config import settings
from app.agents.state import ConversationState, REQUIRED_INFO_CATEGORIES, calculate_confidence_score

# System prompt for the interviewer agent
INTERVIEWER_SYSTEM_PROMPT = """Sos un asistente médico experto realizando una anamnesis (entrevista clínica).

TU ROL:
- Hacer preguntas médicas relevantes y profesionales
- Recopilar información completa del paciente
- Ser empático pero eficiente
- Evaluar si tenés suficiente información para generar un diagnóstico
- No hacer diagnósticos (ese no es tu rol, otro agente lo hará)

PROTOCOLO:
1. Si es el primer turno: preguntá sobre la queja principal
2. Luego explorá sistemáticamente:
   - Síntomas y su evolución (inicio, duración, progresión, severidad)
   - Síntomas asociados
   - Antecedentes médicos
   - Medicaciones actuales
   - Alergias
   - Factores de riesgo relevantes (historia social)

EVALUACIÓN DE COMPLETITUD:
Después de cada respuesta del paciente, evaluá si tenés SUFICIENTE información para que otro agente genere un diagnóstico.

Considerá que tenés SUFICIENTE información cuando:
- Tenés la queja principal claramente identificada
- Conocés el inicio, duración y progresión de los síntomas
- Tenés información sobre la severidad
- Has explorado síntomas asociados relevantes
- Tenés antecedentes médicos y medicaciones (si son relevantes)
- Has hecho al menos 4-5 preguntas sustanciales
- NO hay lagunas críticas de información

NO considerés suficiente información si:
- Es el primer o segundo turno (muy prematuro)
- Hay red flags mencionados que necesitan más exploración
- Faltan detalles críticos sobre síntomas principales
- No conocés datos demográficos básicos (edad, sexo) cuando son relevantes

REGLAS:
- Hacé UNA pregunta a la vez (máximo 2 si están muy relacionadas)
- Usá lenguaje claro y no técnico con el paciente
- NO repitas preguntas ya hechas
- Seguí las guías clínicas cuando sea relevante
- Si el paciente menciona algo preocupante (red flag), preguntá más sobre eso

FORMATO DE RESPUESTA:
Respondé SIEMPRE en formato JSON con esta estructura EXACTA:
{
  "ready_for_diagnosis": true/false,
  "message": "tu mensaje al paciente"
}

Si ready_for_diagnosis es true:
- El mensaje debe ser una transición profesional como: "Gracias por la información. He recopilado suficiente datos para proceder con un análisis diagnóstico completo. Voy a generar una evaluación clínica detallada."

Si ready_for_diagnosis es false:
- El mensaje debe ser tu siguiente pregunta para continuar la anamnesis
- Ejemplo: "¿Desde cuándo comenzaron estos síntomas?"

Respondé SOLO con el JSON válido, sin texto adicional antes o después.
"""

class InterviewerAgent:
    """Agent responsible for conducting the medical interview"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_TEXT,
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        )
    
    async def run(self, state: ConversationState) -> Dict[str, Any]:
        """
        Run the interviewer agent to generate the next question or decide to proceed to diagnosis.
        
        Returns:
            Updated state with new assistant message and ready_for_diagnosis flag
        """
        import json
        
        # Build the prompt
        messages = self._build_messages(state)
        
        # Generate response
        response = await self.llm.ainvoke(messages)
        raw_content = response.content
        
        # Parse JSON response
        try:
            # Try to extract JSON from the response
            response_data = self._parse_json_response(raw_content)
            assistant_message = response_data.get("message", raw_content)
            ready_for_diagnosis = response_data.get("ready_for_diagnosis", False)
        except Exception as e:
            # Fallback: treat as regular message if JSON parsing fails
            assistant_message = raw_content
            ready_for_diagnosis = False
        
        # Update state
        new_messages = state["messages"].copy()
        new_messages.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Update questions asked (only if not ready for diagnosis)
        new_questions_asked = state["questions_asked"].copy()
        if not ready_for_diagnosis:
            new_questions_asked.append(assistant_message)
        
        # Increment turn count
        new_turn_count = state["turn_count"] + 1
        
        return {
            "messages": new_messages,
            "questions_asked": new_questions_asked,
            "turn_count": new_turn_count,
            "last_agent": "interviewer",
            "ready_for_diagnosis": ready_for_diagnosis,
        }
    
    def _build_messages(self, state: ConversationState) -> list:
        """Build the message list for the LLM"""
        messages = [SystemMessage(content=INTERVIEWER_SYSTEM_PROMPT)]
        
        # Add context about what we know so far
        context_info = self._build_context_summary(state)
        messages.append(HumanMessage(content=f"CONTEXTO ACTUAL:\n{context_info}"))
        
        # Add conversation history
        for msg in state["messages"]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add instruction for next action
        messages.append(HumanMessage(
            content="Evaluá si tenés suficiente información. "
                    "Respondé con el formato JSON especificado: {\"ready_for_diagnosis\": true/false, \"message\": \"...\"}. "
                    "Si no estás listo, el mensaje debe ser tu siguiente pregunta. "
                    "Si estás listo, el mensaje debe indicar que vas a proceder con el análisis."
        ))
        
        return messages
    
    def _parse_json_response(self, raw_content: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, handling markdown code blocks if present"""
        import json
        import re
        
        # Try direct JSON parse first
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, raw_content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in the text
        json_pattern = r'\{[^{}]*"ready_for_diagnosis"[^{}]*"message"[^{}]*\}'
        match = re.search(json_pattern, raw_content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        # If all fails, raise exception
        raise ValueError(f"Could not parse JSON from response: {raw_content[:100]}")
    
    def _build_context_summary(self, state: ConversationState) -> str:
        """Build a summary of what information we have collected"""
        parts = []
        
        # Patient info
        if state["patient_info"]:
            info_str = ", ".join([f"{k}: {v}" for k, v in state["patient_info"].items()])
            parts.append(f"Información del paciente: {info_str}")
        
        # Symptoms
        if state["symptoms"]:
            parts.append(f"Síntomas mencionados: {', '.join(state['symptoms'])}")
        
        # Categories covered
        covered = [cat for cat, done in state["info_categories_covered"].items() if done]
        missing = [cat for cat, done in state["info_categories_covered"].items() if not done]
        
        if covered:
            parts.append(f"Categorías cubiertas: {', '.join(covered)}")
        
        if missing:
            parts.append(f"Categorías faltantes: {', '.join(missing[:5])}")  # Show first 5
        
        # Turn count
        parts.append(f"Turno: {state['turn_count']}/{settings.MAX_INTERVIEW_TURNS}")
        
        # Confidence
        parts.append(f"Completitud: {state['confidence_score']:.0%}")
        
        return "\n".join(parts)
    
    async def process_user_response(self, state: ConversationState) -> Dict[str, Any]:
        """
        Process the user's response to extract information.
        This updates patient_info, symptoms, and categories_covered.
        """
        if not state["messages"]:
            return {}
        
        # Get the last user message
        last_user_msg = None
        for msg in reversed(state["messages"]):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break
        
        if not last_user_msg:
            return {}
        
        # Use LLM to extract structured information
        extraction_result = await self._extract_information(last_user_msg, state)
        
        # Update patient info
        new_patient_info = {**state["patient_info"], **extraction_result.get("patient_info", {})}
        
        # Update symptoms
        new_symptoms = state["symptoms"].copy()
        for symptom in extraction_result.get("symptoms", []):
            if symptom not in new_symptoms:
                new_symptoms.append(symptom)
        
        # Update categories covered
        new_categories = state["info_categories_covered"].copy()
        for category in extraction_result.get("categories", []):
            if category in new_categories:
                new_categories[category] = True
        
        # Calculate new confidence score
        temp_state = {**state, "info_categories_covered": new_categories, "symptoms": new_symptoms, "patient_info": new_patient_info}
        new_confidence = calculate_confidence_score(temp_state)
        
        return {
            "patient_info": new_patient_info,
            "symptoms": new_symptoms,
            "info_categories_covered": new_categories,
            "confidence_score": new_confidence,
        }
    
    async def _extract_information(self, user_message: str, state: ConversationState) -> Dict[str, Any]:
        """Use LLM to extract structured information from user response"""
        
        extraction_prompt = f"""Analizá esta respuesta del paciente y extraé información estructurada.

Respuesta del paciente: "{user_message}"

Contexto previo:
- Síntomas ya mencionados: {', '.join(state['symptoms']) if state['symptoms'] else 'ninguno'}
- Info del paciente: {state['patient_info']}

Extraé y devolvé en formato JSON:
{{
  "symptoms": ["lista", "de", "nuevos", "síntomas"],
  "patient_info": {{"edad": 45, "sexo": "M", etc}},
  "categories": ["chief_complaint", "symptom_onset", etc]
}}

Categorías disponibles: {', '.join(REQUIRED_INFO_CATEGORIES.keys())}

Respondé SOLO con el JSON, sin texto adicional.
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            
            # Parse JSON response - handle markdown code blocks
            import json
            import re
            
            content = response.content.strip()
            
            # Try to extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            # Remove any leading/trailing text before/after braces
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            result = json.loads(content)
            
            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Result is not a dictionary")
            
            # Ensure required keys exist
            result.setdefault("symptoms", [])
            result.setdefault("patient_info", {})
            result.setdefault("categories", [])
            
            return result
            
        except Exception as e:
            # If extraction fails, log and return empty
            print(f"⚠️  Warning: Failed to extract information: {str(e)}")
            print(f"   Raw response: {response.content if 'response' in locals() else 'N/A'}")
            return {"symptoms": [], "patient_info": {}, "categories": []}


# Singleton instance
interviewer_agent = InterviewerAgent()
