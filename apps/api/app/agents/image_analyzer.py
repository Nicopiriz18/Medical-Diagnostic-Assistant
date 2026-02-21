"""
Image Analyzer Agent: Analyzes medical images using GPT-4o Vision.
Extracts visual findings and integrates them into the diagnostic context.
"""

from typing import Dict, Any, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.agents.state import ConversationState
import base64
from pathlib import Path
import httpx

IMAGE_ANALYSIS_PROMPT = """Sos un asistente médico especializado en análisis de imágenes clínicas.

IMPORTANTE - DISCLAIMER:
- Esta es una herramienta de APOYO, no un diagnóstico definitivo
- Las imágenes deben ser evaluadas por un profesional médico
- No reemplazás el juicio clínico de un especialista

TU TAREA:
Analizar la imagen médica provista y describir hallazgos visuales objetivos.

ENFOQUE:
1. Describe lo que ves de manera objetiva
2. Identifica características relevantes (color, forma, tamaño, localización)
3. Menciona hallazgos que puedan ser clínicamente significativos
4. Si reconocés patrones específicos, mencionálos

TIPOS DE IMÁGENES:
- Lesiones dermatológicas: color, bordes, simetría, diámetro, evolución
- Fotos de síntomas visibles: inflamación, edema, deformidad, etc.
- Radiografías: estructuras, densidades, anomalías (con disclaimer de que requiere radiólogo)

FORMATO DE RESPUESTA:
Devolvé un objeto JSON con:
{{
  "description": "Descripción objetiva de lo visible",
  "findings": ["hallazgo 1", "hallazgo 2", ...],
  "clinical_relevance": "Posible relevancia clínica de estos hallazgos",
  "requires_specialist": true/false,
  "specialist_type": "tipo de especialista recomendado si aplica",
  "disclaimer": "Limitaciones de este análisis"
}}

Respondé SOLO con JSON válido, sin markdown ni texto adicional.
"""

class ImageAnalyzerAgent:
    """Agent responsible for analyzing medical images"""
    
    def __init__(self):
        import logging
        logger = logging.getLogger(__name__)
        
        # Validate API key is configured
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not configured!")
            raise ValueError(
                "OPENAI_API_KEY must be configured for image analysis. "
                "Please set OPENAI_API_KEY in your .env file."
            )
        
        logger.info(f"Initializing ImageAnalyzerAgent with model: {settings.OPENAI_MODEL_VISION}")
        
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_VISION,
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )
    
    async def analyze_image(
        self,
        image_url: str,
        context: str = "",
        local_path: Path = None
    ) -> Dict[str, Any]:
        """
        Analyze a single medical image.
        
        Args:
            image_url: URL or path to the image
            context: Clinical context (symptoms, patient info)
            local_path: Local file path if available
        
        Returns:
            Analysis results as dict
        """
        # Prepare the image for GPT-4o Vision
        if local_path and local_path.exists():
            # Read local file and encode
            image_data = await self._encode_local_image(local_path)
        else:
            # Use URL directly
            image_data = image_url
        
        # Build the prompt with context
        full_prompt = IMAGE_ANALYSIS_PROMPT
        
        if context:
            full_prompt += f"\n\nCONTEXTO CLÍNICO:\n{context}"
        
        # Create message with image
        message = HumanMessage(
            content=[
                {"type": "text", "text": full_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data if isinstance(image_data, str) else f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        )
        
        # Get analysis
        import logging
        import json
        
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Calling OpenAI Vision API for image analysis")
            response = await self.llm.ainvoke([message])
            logger.info("Received response from OpenAI Vision API")
            
            # Parse JSON response
            analysis = json.loads(response.content)
            
            return analysis
        
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return raw response
            logger.warning(f"Failed to parse JSON response from Vision API: {str(e)}")
            logger.warning(f"Raw response: {response.content[:500]}")
            return {
                "description": response.content,
                "findings": [],
                "clinical_relevance": "Unable to parse structured analysis",
                "requires_specialist": True,
                "specialist_type": "physician",
                "disclaimer": "Analysis format error - review manually"
            }
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            
            logger.error(f"Error analyzing image: {error_type} - {error_message}")
            
            # Check for specific OpenAI API errors
            if "authentication" in error_message.lower() or "api_key" in error_message.lower():
                logger.error("OpenAI API authentication failed - check API key")
                raise ValueError(
                    "OpenAI API authentication failed. Please verify your API key is valid."
                )
            elif "rate_limit" in error_message.lower() or "quota" in error_message.lower():
                logger.error("OpenAI API rate limit exceeded")
                raise ValueError(
                    "OpenAI API rate limit exceeded. Please try again later."
                )
            elif "timeout" in error_message.lower():
                logger.error("OpenAI API request timed out")
                raise ValueError(
                    "Request to OpenAI API timed out. Please try again."
                )
            else:
                # Generic error - re-raise with more context
                logger.error(f"Unexpected error during image analysis: {error_message}")
                raise ValueError(
                    f"Error analyzing image with OpenAI Vision API: {error_message}"
                )
    
    async def _encode_local_image(self, image_path: Path) -> str:
        """Encode local image to base64"""
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        import base64
        return base64.b64encode(image_bytes).decode('utf-8')
    
    async def run(self, state: ConversationState, new_image_url: str) -> Dict[str, Any]:
        """
        Run the image analyzer agent on a new image.
        
        Args:
            state: Current conversation state
            new_image_url: URL of the newly uploaded image
        
        Returns:
            Updated state with image analysis
        """
        from app.services.storage import storage_service
        
        # Build clinical context
        context = self._build_clinical_context(state)
        
        # Get local path if using local storage
        local_path = storage_service.get_image_path(new_image_url)
        
        # Analyze the image
        analysis = await self.analyze_image(
            image_url=new_image_url,
            context=context,
            local_path=local_path
        )
        
        # Add to images list
        new_images = state["images"].copy()
        new_images.append({
            "url": new_image_url,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Extract any new symptoms from image findings
        new_symptoms = state["symptoms"].copy()
        for finding in analysis.get("findings", []):
            # Simple heuristic: if finding is not already in symptoms, add it
            if finding not in new_symptoms and len(finding) < 50:
                new_symptoms.append(finding)
        
        # Create a message summarizing the analysis
        summary = self._create_analysis_summary(analysis)
        
        new_messages = state["messages"].copy()
        new_messages.append({
            "role": "assistant",
            "content": summary
        })
        
        return {
            "images": new_images,
            "symptoms": new_symptoms,
            "messages": new_messages,
            "last_agent": "image_analyzer",
        }
    
    def _build_clinical_context(self, state: ConversationState) -> str:
        """Build clinical context string for image analysis"""
        parts = []
        
        if state["symptoms"]:
            parts.append(f"Síntomas: {', '.join(state['symptoms'])}")
        
        if state["patient_info"]:
            info_str = ", ".join([f"{k}: {v}" for k, v in state["patient_info"].items()])
            parts.append(f"Paciente: {info_str}")
        
        # Recent conversation
        if state["messages"]:
            recent = state["messages"][-2:]
            recent_text = " | ".join([msg["content"][:100] for msg in recent])
            parts.append(f"Conversación reciente: {recent_text}")
        
        return "\n".join(parts) if parts else "Sin contexto previo"
    
    def _create_analysis_summary(self, analysis: Dict[str, Any]) -> str:
        """Create a natural language summary of the image analysis"""
        summary_parts = [
            "He analizado la imagen que subiste.",
            f"\n{analysis.get('description', 'No se pudo generar descripción.')}",
        ]
        
        if analysis.get("findings"):
            findings_str = ", ".join(analysis["findings"])
            summary_parts.append(f"\nHallazgos notables: {findings_str}")
        
        if analysis.get("clinical_relevance"):
            summary_parts.append(f"\nRelevancia clínica: {analysis['clinical_relevance']}")
        
        if analysis.get("requires_specialist"):
            specialist = analysis.get("specialist_type", "médico especialista")
            summary_parts.append(f"\n⚠️ Se recomienda evaluación por {specialist}.")
        
        summary_parts.append(
            f"\n\n⚕️ Recordá: {analysis.get('disclaimer', 'Este análisis es solo de apoyo y no reemplaza evaluación médica profesional.')}"
        )
        
        return " ".join(summary_parts)


# Singleton instance
image_analyzer_agent = ImageAnalyzerAgent()
