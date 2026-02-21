# Guía del Frontend - Interfaz de Chat

El frontend ha sido completamente actualizado para usar el nuevo sistema de agentes con imágenes.

## 🎨 Características del Nuevo Frontend

### ✅ Interfaz de Chat Conversacional
- Diseño tipo ChatGPT moderno y limpio
- Mensajes del usuario (azul) y asistente (blanco)
- Avatares y timestamps en cada mensaje
- Auto-scroll automático a nuevos mensajes
- Animaciones suaves

### ✅ Gestión de Sesiones
- Creación automática de sesión al cargar la página
- Indicador de estado (Activa/Completada)
- Botón "Nueva Conversación" para reiniciar
- Persistencia de session_id

### ✅ Subida de Imágenes
- Botón de adjuntar (📎) en el input
- Preview de imagen subida
- Indicador de "Analizando imagen..."
- Imágenes mostradas en el historial
- Click en imagen para ver en tamaño completo

### ✅ Análisis con Agentes
- Respuestas inteligentes del agente entrevistador
- Preguntas adaptativas al contexto
- Extracción automática de síntomas
- Indicador "escribiendo..." mientras procesa

### ✅ Visualización de Diagnóstico
- Panel destacado con evaluación completa
- Secciones expandibles/colapsables:
  - 📋 Resumen del Paciente
  - 🎯 Diagnósticos Diferenciales (con % y urgencia)
  - 🚨 Señales de Alerta (red flags)
  - ✅ Plan de Acción
  - 📝 Nota SOAP
  - ❓ Información Adicional
  - ⚠️ Limitaciones
- Botón "Forzar Diagnóstico" después de varias preguntas

### ✅ UX Mejorada
- Mensaje de bienvenida del agente
- Botones de acciones rápidas al inicio
- Loading states claros
- Manejo de errores con mensajes amigables
- Confirmación antes de finalizar
- Responsive (funciona en móvil)

## 🚀 Cómo Usar

### 1. Iniciar el Sistema

```bash
# Asegúrate de tener el .env configurado
# Inicia todo con docker-compose
docker-compose up -d

# El frontend estará en:
# http://localhost:3000
```

### 2. Flujo de Uso

1. **Página carga automáticamente** → Crea sesión
2. **Mensaje de bienvenida** del asistente aparece
3. **Opciones rápidas** para comenzar (opcional)
4. **Escribe tu consulta** en el input inferior
5. **Presiona Enter o clic en Enviar**
6. **Agente responde** con preguntas relevantes
7. **Responde las preguntas** del agente
8. **(Opcional) Sube imágenes** con el botón 📎
9. **Continúa la conversación** hasta tener suficiente info
10. **Genera diagnóstico:**
    - Automático: el agente decide cuando está listo
    - Manual: clic en "Generar Diagnóstico Completo"
11. **Revisa el análisis** en el panel expandible
12. **Nueva Conversación** para otro caso

### 3. Ejemplo de Conversación

```
Usuario: "Hola, tengo dolor de cabeza intenso desde hace 2 días"
Agente: "Entiendo que tienes dolor de cabeza desde hace 2 días. 
         Para ayudarte mejor, ¿podrías describir el dolor? 
         ¿Es pulsátil, opresivo, punzante?"

Usuario: "Es pulsátil, principalmente del lado derecho"
Agente: "¿El dolor está acompañado de náuseas, vómitos o 
         sensibilidad a la luz?"

Usuario: "Sí, náuseas y me molesta mucho la luz"
Agente: "¿Has tenido episodios similares antes? ¿Cuántos años tienes?"

Usuario: "Sí, esto me pasa cada mes más o menos. Tengo 28 años"
Agente: "¿Algún antecedente médico relevante? ¿Tomas algún medicamento?"

Usuario: "No, ningún antecedente importante"

[Aparece botón "Generar Diagnóstico Completo"]
[Usuario hace clic]

Agente: "📋 He generado la evaluación diagnóstica completa..."

[Aparece panel con diagnóstico detallado]
```

## 📸 Subir Imágenes

1. Clic en el botón 📎 (clip) junto al input
2. Selecciona imagen (JPG, PNG, etc.)
3. Imagen se sube automáticamente
4. Aparece "Analizando imagen..." con spinner
5. Agente responde con análisis de la imagen
6. Continúa la conversación normalmente

## 🎯 Componentes Creados

### `ChatMessage.tsx`
- Muestra mensajes individuales
- Maneja avatares, timestamps
- Muestra imágenes adjuntas
- Soporte para formato de texto

### `ChatInput.tsx`
- Input de texto con auto-resize
- Botón de adjuntar imagen
- Botón de enviar
- Soporte para Shift+Enter (nueva línea)
- Estados disabled mientras procesa

### `DiagnosticPanel.tsx`
- Panel completo del diagnóstico
- Secciones expandibles/colapsables
- Colores según urgencia/severidad
- Mantiene el diseño del frontend original

### `ImagePreview.tsx`
- Preview de imagen subida
- Indicador de análisis en progreso
- Botón para eliminar (si aplica)

## 🎨 Diseño Visual

- **Colores principales:**
  - Usuario: `#2563eb` (azul)
  - Asistente: blanco con borde
  - Urgencias: rojo/naranja/verde
  - Fondo: `#f9fafb` (gris claro)

- **Tipografía:** system-ui (nativa del sistema)
- **Bordes:** redondeados (border-radius: 8-24px)
- **Sombras:** sutiles para profundidad
- **Animaciones:** suaves (0.2-0.3s)

## 📱 Responsive

El diseño es responsive y funciona en:
- ✅ Desktop (óptimo)
- ✅ Tablet (adaptado)
- ✅ Móvil (funcional)

En móvil:
- Chat ocupa altura completa
- Input se adapta al teclado
- Botones táctiles grandes
- Imágenes escaladas apropiadamente

## 🔧 Configuración

El frontend usa la variable de entorno:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Configurada en `docker-compose.yml` y `next.config.js`.

## 🐛 Troubleshooting

### "Error al crear la sesión"
- Verifica que la API esté corriendo (`docker-compose ps`)
- Verifica que el puerto 8000 esté accesible
- Revisa los logs: `docker-compose logs api`

### "Error al enviar el mensaje"
- Verifica conexión con la API
- Revisa que la sesión sea válida
- Mira la consola del navegador (F12)

### Imagen no se sube
- Verifica formato (JPG, PNG permitidos)
- Verifica tamaño (máx 10MB)
- Revisa logs del servidor

### Frontend no carga
```bash
# Reconstruir el frontend
docker-compose build web
docker-compose up -d web

# Ver logs
docker-compose logs -f web
```

## 🔄 Desarrollo Local

Si quieres desarrollar el frontend sin Docker:

```bash
cd apps/api/web

# Instalar dependencias
npm install

# Configurar URL de la API
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Correr en modo desarrollo
npm run dev

# Acceder a http://localhost:3000
```

## 📝 Notas Importantes

1. **Sesiones:** Cada pestaña del navegador = nueva sesión
2. **Historial:** No se guarda entre recargas (por ahora)
3. **Imágenes:** Se guardan en el servidor (local o S3)
4. **Diagnóstico:** Solo se genera una vez por sesión
5. **Nueva conversación:** Crea una sesión completamente nueva

## 🚀 Próximas Mejoras Posibles

- [ ] Guardar historial de sesiones en localStorage
- [ ] Recuperar sesión anterior al recargar
- [ ] Exportar diagnóstico como PDF
- [ ] Compartir diagnóstico (con seguridad)
- [ ] Modo oscuro
- [ ] Historial de sesiones anteriores
- [ ] Búsqueda en el historial
- [ ] Notificaciones push cuando el agente responde

## 🎉 ¡Listo!

El frontend está completamente funcional y conectado con el sistema de agentes.

**Para probarlo:**
```bash
docker-compose up -d
# Abre http://localhost:3000
```

Disfruta de tu asistente médico inteligente! 🏥✨
