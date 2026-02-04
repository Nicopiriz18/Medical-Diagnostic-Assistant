import json
from pydantic import ValidationError
from app.core.config import settings
from app.models.clinical import ClinicalAssessment
from app.services.llm import LLMClient

SYSTEM_PROMPT = """Sos un asistente clínico para profesionales.
No reemplazás juicio médico. No das órdenes finales.
Tu tarea: generar un análisis estructurado para apoyar el razonamiento diagnóstico.

REGLAS DE SALIDA:
- Respondé SOLO con JSON válido (sin markdown, sin texto extra).
- Ajustate exactamente al esquema pedido.
- Likelihood 0-100 es heurístico, NO probabilidad real.
- Si faltan datos, agregá preguntas faltantes en missing_questions.
"""

def build_user_prompt(case_text: str) -> str:
    return f"""Caso clínico (texto libre):
{case_text}

Generá un objeto JSON que matchee este esquema (respetar claves):
{{
  "differentials": [{{"name": "...", "likelihood": 0, "reasoning": "...", "urgency": "immediate|urgent|routine"}}],
  "red_flags": [{{"severity":"critical|warning|info","message":"...","why_it_matters":"..."}}],
  "missing_questions": ["..."],
  "action_plan": [{{"priority":"immediate|urgent|routine","action":"...","rationale":"..."}}],
  "soap": {{"subjective":"...","objective":"...","assessment":"...","plan":"..."}},
  "patient_summary": "...",
  "limitations": "..."
}}
"""

async def analyze_case(case_text: str) -> ClinicalAssessment:
    llm = LLMClient()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(case_text)},
    ]

    raw = await llm.chat(messages=messages, model=settings.LLM_MODEL, temperature=0.2)

    # 1) parseo directo
    try:
        obj = json.loads(raw)
        return ClinicalAssessment.model_validate(obj)
    except (json.JSONDecodeError, ValidationError):
        # 2) intento de reparación (una vez)
        repair_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(case_text)},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "El output anterior no es JSON válido o no matchea el esquema. Devolvé SOLO JSON válido acorde al esquema."},
        ]
        fixed = await llm.chat(messages=repair_messages, model=settings.LLM_MODEL, temperature=0.0)
        obj2 = json.loads(fixed)
        return ClinicalAssessment.model_validate(obj2)
