# Implementación de Diagnóstico Automático

## Resumen

Se ha implementado exitosamente la funcionalidad de **diagnóstico automático inteligente**, donde el agente de entrevista (interviewer) evalúa dinámicamente si tiene suficiente información para proceder con un diagnóstico y finaliza la conversación automáticamente cuando está listo.

## Cambios Realizados

### 1. Agente de Entrevista (`apps/api/app/agents/interviewer.py`)

#### Cambios en el Prompt del Sistema
- Se actualizó `INTERVIEWER_SYSTEM_PROMPT` para incluir instrucciones sobre cuándo considerar que hay suficiente información
- El agente ahora evalúa después de cada respuesta si puede proceder al diagnóstico
- Se establecieron criterios claros: queja principal, evolución temporal, severidad, síntomas asociados, y mínimo 4-5 preguntas

#### Formato de Respuesta Estructurado
- El agente ahora responde en formato JSON:
  ```json
  {
    "ready_for_diagnosis": true/false,
    "message": "mensaje al paciente"
  }
  ```
- Si `ready_for_diagnosis=true`, el mensaje indica que procederá con el análisis
- Si `ready_for_diagnosis=false`, el mensaje es la siguiente pregunta

#### Nuevo Método `_parse_json_response()`
- Parsea respuestas JSON del LLM
- Maneja múltiples formatos: JSON directo, bloques de código markdown, etc.
- Incluye lógica de fallback en caso de error

#### Modificaciones en `run()`
- Procesa la respuesta estructurada del LLM
- Extrae el flag `ready_for_diagnosis` y el mensaje
- Actualiza el estado con el flag para indicar que está listo para diagnóstico

### 2. Lógica de Routing (`apps/api/app/agents/graph.py`)

#### `route_from_interviewer()`
- **Prioridad 1**: Si `ready_for_diagnosis=True`, ir directamente al nodo `diagnostic`
- **Prioridad 2**: Chequeo periódico cada 3 turnos (como respaldo)
- **Default**: Finalizar turno y esperar respuesta del usuario

```python
def route_from_interviewer(state: ConversationState) -> str:
    # Interviewer decidió que está listo
    if state.get("ready_for_diagnosis", False):
        return "diagnostic"
    
    # Chequeo periódico como respaldo
    if state["turn_count"] % 3 == 0 and state["turn_count"] > 0:
        return "ready_check"
    
    # Continuar entrevista
    return END
```

### 3. Orquestador (`apps/api/app/agents/orchestrator.py`)

#### `decide_next_node()`
- Prioriza el flag `ready_for_diagnosis` establecido por el interviewer
- Mantiene compatibilidad con chequeos automáticos de completitud
- Respeta el límite máximo de turnos

### 4. Criterios de Completitud Mejorados (`apps/api/app/agents/state.py`)

#### `should_proceed_to_diagnosis()`
Función de respaldo con criterios más robustos:

**Condiciones para proceder:**
1. **Mínimo 4 turnos** (evita diagnósticos prematuros)
2. **Categorías críticas cubiertas**: chief_complaint, symptom_onset, severity
3. **Síntomas identificados**: Al menos un síntoma registrado
4. **Confidence score** ≥ 0.7 (configurable)
5. **Categorías recomendadas**: symptom_duration o associated_symptoms (opcional con alta confianza)

**Bypass por alta confianza:**
- Si confidence ≥ 0.85, puede proceder incluso sin categorías recomendadas

**Forced completion:**
- Al alcanzar `MAX_INTERVIEW_TURNS`, se fuerza el diagnóstico

### 5. Endpoint Manual Preservado (`apps/api/app/main.py`)

El endpoint `/v1/sessions/{session_id}/finalize` se mantiene intacto:
- Permite al usuario forzar el diagnóstico cuando lo desee
- Funciona independientemente del sistema automático
- Útil para casos donde el usuario quiere finalizar antes de tiempo

## Flujo de Ejecución

```
Usuario envía mensaje
    ↓
Interviewer procesa y extrae información
    ↓
Interviewer evalúa completitud
    ↓
    ├─→ [Suficiente] → ready_for_diagnosis = True
    │       ↓
    │   Mensaje: "Voy a generar el diagnóstico"
    │       ↓
    │   Routing: diagnostic → Diagnóstico completo
    │
    └─→ [Necesita más] → ready_for_diagnosis = False
            ↓
        Mensaje: Siguiente pregunta
            ↓
        Espera respuesta del usuario
```

## Flujo Alternativo (Manual)

```
Usuario presiona "Finalizar"
    ↓
POST /v1/sessions/{id}/finalize
    ↓
force_diagnosis() establece ready_for_diagnosis = True
    ↓
Diagnóstico generado inmediatamente
```

## Pruebas Realizadas

Se verificaron los siguientes aspectos:

### ✓ Parsing de Respuestas JSON
- JSON directo
- JSON en bloques de código markdown
- JSON sin etiqueta de lenguaje

### ✓ Lógica de Routing
- Flag `ready_for_diagnosis` tiene prioridad máxima
- Chequeo periódico funciona como respaldo
- Routing correcto en diferentes estados

### ✓ Criterios de Completitud
- Mínimo de turnos previene diagnósticos prematuros
- Categorías críticas son obligatorias
- Alta confianza puede bypass categorías opcionales

### ✓ Decisiones del Orquestador
- Respeta el flag del interviewer
- Maneja estados iniciales correctamente
- Finaliza apropiadamente con assessment completo

## Ventajas de la Implementación

1. **Experiencia Natural**: El agente decide cuándo tiene suficiente información, como un médico real
2. **Flexibilidad**: Adapta la duración de la entrevista según la complejidad del caso
3. **Control del Usuario**: Mantiene la opción de forzar el diagnóstico manualmente
4. **Seguridad Clínica**: 
   - Mínimo de turnos previene diagnósticos apresurados
   - Categorías críticas son obligatorias
   - Red flags pueden extender la entrevista
5. **Eficiencia**: Evita preguntas innecesarias cuando ya hay información suficiente

## Configuración

Las siguientes variables en `app/core/config.py` controlan el comportamiento:

- `MAX_INTERVIEW_TURNS`: Límite máximo de turnos (default: 20)
- `CONFIDENCE_THRESHOLD`: Umbral de confianza para proceder (default: 0.7)

## Compatibilidad

- ✓ Compatible con el endpoint manual `/finalize`
- ✓ No rompe flujos existentes
- ✓ Mantiene chequeos periódicos como respaldo
- ✓ Frontend existente sigue funcionando sin cambios

## Notas Importantes

1. El LLM (GPT-4) es responsable de la evaluación de completitud principal
2. Existen mecanismos de respaldo en caso de que el LLM no establezca el flag
3. El sistema prioriza seguridad clínica sobre eficiencia
4. Los disclaimers sobre evaluación médica profesional se mantienen en todos los diagnósticos
