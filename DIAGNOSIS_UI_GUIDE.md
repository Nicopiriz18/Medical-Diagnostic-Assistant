# Guía Visual: Nueva Experiencia de Diagnóstico

## Vista Previa del Proceso

### 1. Estado Inicial
```
┌────────────────────────────────────────────────┐
│  ¿Ya tienes suficiente información para el     │
│  diagnóstico?                                  │
│                                                │
│  ┌──────────────────────────────────────┐     │
│  │  📋 Generar Diagnóstico Completo     │     │
│  └──────────────────────────────────────┘     │
└────────────────────────────────────────────────┘
```

### 2. Durante el Análisis (Fases)

```
┌────────────────────────────────────────────────┐
│  🧠 Análisis Clínico en Progreso               │
│                                                │
│  ⭕ Consultando base de conocimiento médico    │
│     y casos similares...                       │
│                                                │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░         │
│                                                │
│  Este proceso puede tomar entre 10-15          │
│  segundos...                                   │
└────────────────────────────────────────────────┘
```

**Progresión de mensajes:**
1. ⏳ "Revisando información del caso y síntomas presentados..."
2. 📚 "Consultando base de conocimiento médico y casos similares..."
3. 🔍 "Analizando diagnósticos diferenciales y evaluando probabilidades..."
4. 📝 "Generando evaluación clínica estructurada y plan de acción..."
5. ✅ "Finalizando evaluación y preparando recomendaciones..."

### 3. Diagnóstico Completado

```
┌────────────────────────────────────────────────┐
│  📋 He generado la evaluación diagnóstica      │
│  completa. Revisa el panel a continuación con  │
│  todos los detalles.                           │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  📋 EVALUACIÓN DIAGNÓSTICA                     │
│                                                │
│  Diagnósticos Diferenciales                    │
│  1. [Diagnóstico principal]                    │
│  2. [Diagnóstico alternativo]                  │
│  ...                                           │
└────────────────────────────────────────────────┘
```

## Comparación: Antes vs Después

### ❌ ANTES (Instantáneo)
```
Click → 💨 POOF! → Diagnóstico aparece

Duración: < 1 segundo
Sensación: Demasiado rápido, poco confiable
```

### ✅ DESPUÉS (Reflexivo)
```
Click → Confirmación → 
  Fase 1 (2.5s) → 
  Fase 2 (2.0s) → 
  Fase 3 (2.5s) → 
  Fase 4 (3-5s) → 
  Fase 5 (1.5s) → 
  Diagnóstico completo

Duración total: 10-15 segundos
Sensación: Análisis profundo y profesional
```

## Elementos Visuales Clave

### 🎨 Colores y Estilo
- **Panel de progreso**: Fondo blanco con borde azul (#3b82f6)
- **Spinner**: Círculo animado con rotación
- **Barra de progreso**: Gradiente azul (#3b82f6 → #60a5fa)
- **Texto**: 
  - Título en azul oscuro (#1e40af)
  - Mensaje en gris (#6b7280)
  - Nota en gris claro (#9ca3af)

### ⚡ Animaciones
1. **Spinner**: Rotación continua (360° en 1 segundo)
2. **Barra de progreso**: Movimiento de izquierda a derecha
3. **Transiciones**: Suaves entre fases

### 📱 Responsive
- Funciona en desktop y móvil
- Diseño centrado y bien espaciado
- Tipografía legible y profesional

## Flujo de Interacción del Usuario

```
┌─────────────────────────────────────┐
│ Usuario revisa la conversación      │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Click en "Generar Diagnóstico"      │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Diálogo de confirmación             │
│ "¿Estás seguro...?"                 │
└────────────┬────────────────────────┘
             │
             ↓ [Acepta]
┌─────────────────────────────────────┐
│ Panel de progreso aparece           │
│ Botón se deshabilita                │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Fase 1: Revisión (2.5s)            │
│ [Mensaje actualizado]               │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Fase 2: Consulta de conocimiento   │
│ médico (2.0s)                       │
│ [Mensaje actualizado]               │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Fase 3: Análisis (2.5s)            │
│ [Mensaje actualizado]               │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Fase 4: Generación LLM (3-5s)      │
│ [Mensaje actualizado]               │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Fase 5: Finalización (1.5s)        │
│ [Mensaje actualizado]               │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Panel de diagnóstico completo       │
│ Sesión marcada como completada      │
└─────────────────────────────────────┘
```

## Mensajes de Error

Si algo falla durante el proceso:

```
┌────────────────────────────────────────────────┐
│  ❌ Error al generar el diagnóstico            │
└────────────────────────────────────────────────┘
```

El sistema:
- Cierra la conexión SSE
- Muestra mensaje de error
- Permite reintentar
- No pierde el estado de la conversación

## Testing Manual

### Casos a probar:
1. ✅ **Happy path**: Diagnóstico se genera correctamente
2. ❌ **Error de red**: Simular desconexión
3. 🔄 **Cancelación**: Usuario cierra pestaña durante análisis
4. 📱 **Móvil**: Funciona en dispositivos móviles
5. 🐢 **Conexión lenta**: Comportamiento con latencia alta

### Checklist:
- [ ] Las 5 fases aparecen en orden
- [ ] Cada fase toma el tiempo esperado
- [ ] El spinner gira suavemente
- [ ] La barra de progreso se anima
- [ ] El diagnóstico final se muestra correctamente
- [ ] No hay errores en consola del navegador
- [ ] Funciona en Chrome, Firefox, Safari
- [ ] Responsive en móvil

## Notas Técnicas

### Server-Sent Events (SSE)
- Protocolo: HTTP/1.1
- Content-Type: `text/event-stream`
- Eventos: `progress`, `complete`, `error`
- Reconexión automática del navegador si se pierde la conexión

### Performance
- Tiempo total controlado: ~10-15 segundos
- No bloquea la UI del navegador
- Manejo eficiente de memoria
- Sin polling innecesario
