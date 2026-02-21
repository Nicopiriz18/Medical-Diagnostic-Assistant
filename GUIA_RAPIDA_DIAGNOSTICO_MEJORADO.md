# Guía Rápida: Sistema de Diagnóstico Mejorado

## 🎉 ¡Sistema Mejorado Exitosamente!

El sistema de diagnóstico ahora incluye **información clínica detallada** para cada diagnóstico diferencial.

## 🚀 Cómo Usar

### 1. Iniciar el Sistema

```bash
docker-compose up -d
```

### 2. Acceder a la Interfaz

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 3. Generar un Diagnóstico

1. Abre http://localhost:3000
2. Inicia una conversación describiendo síntomas
3. Responde a las preguntas del agente entrevistador
4. El sistema generará automáticamente el diagnóstico cuando tenga suficiente información
5. O presiona "Generar Diagnóstico Completo" para forzar la generación

### 4. Ver Información Detallada

Cada diagnóstico diferencial ahora muestra:

- **Vista compacta** (por defecto):
  - Nombre del diagnóstico
  - Probabilidad (%)
  - Nivel de urgencia
  - Razonamiento breve

- **Vista expandida** (haz clic en "Ver detalles completos"):
  - 🧬 Causas generales
  - 👤 Factores específicos del paciente
  - ⚠️ Factores de riesgo
  - ✓ Hallazgos que apoyan el diagnóstico
  - ✗ Hallazgos que contradicen el diagnóstico
  - 📊 Pronóstico
  - 🚨 Posibles complicaciones
  - 🔬 Exámenes recomendados
  - 💊 Opciones de tratamiento

## 📋 Ejemplo de Uso

### Caso de Prueba:

**Síntomas:**
- "Tengo 45 años y desde hace 3 días tengo un dolor de cabeza muy fuerte del lado derecho"
- "El dolor es pulsátil y empeora con la luz. También tengo náuseas"
- "No he tenido fiebre. Tomo café todos los días pero estos últimos días no he tomado"
- "Tengo antecedentes de migrañas hace años, pero habían mejorado"

**Resultado:**
- El sistema genera 2-3 diagnósticos diferenciales
- Cada uno con información completa y detallada
- Recomendaciones específicas de exámenes y tratamiento

## 🔧 API Endpoints

### Crear Sesión
```bash
POST http://localhost:8000/v1/sessions
Content-Type: application/json

{
  "user_id": "optional",
  "patient_info": {}
}
```

### Enviar Mensaje
```bash
POST http://localhost:8000/v1/sessions/{session_id}/messages
Content-Type: application/json

{
  "content": "Tengo dolor de cabeza intenso..."
}
```

### Forzar Diagnóstico
```bash
POST http://localhost:8000/v1/sessions/{session_id}/finalize
```

### Obtener Diagnóstico
```bash
GET http://localhost:8000/v1/sessions/{session_id}/diagnosis
```

## 📊 Campos del Diagnóstico

Cada diagnóstico diferencial ahora incluye:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | string | Nombre del diagnóstico |
| `likelihood` | number (0-100) | Probabilidad heurística |
| `reasoning` | string | Razonamiento clínico |
| `urgency` | "immediate"\|"urgent"\|"routine" | Nivel de urgencia |
| `general_causes` | string[] | Causas médicas generales |
| `patient_specific_factors` | string[] | Factores del paciente |
| `risk_factors` | string[] | Factores de riesgo |
| `supporting_findings` | string[] | Hallazgos que apoyan |
| `contradicting_findings` | string[] | Hallazgos que contradicen |
| `prognosis` | string | Pronóstico esperado |
| `complications` | string[] | Complicaciones posibles |
| `recommended_tests` | string[] | Exámenes recomendados |
| `treatment_summary` | string | Resumen de tratamiento |

## ⚠️ Notas Importantes

1. **No es un dispositivo médico:** Este sistema es de apoyo para profesionales de la salud
2. **Requiere validación:** Todos los diagnósticos deben ser validados por profesionales
3. **Limitaciones:** El análisis se basa en información limitada y conversacional
4. **Evaluación presencial:** Siempre necesaria para confirmar diagnósticos

## 🐛 Solución de Problemas

### Los contenedores no inician
```bash
docker-compose down
docker-compose up -d --build
```

### El API no responde
```bash
docker logs medical-diagnostic-assistant-api-1 --tail 50
```

### El frontend no se actualiza
```bash
docker-compose restart web
```

### Verificar salud del sistema
```bash
curl http://localhost:8000/health
# Debe devolver: {"ok":true}
```

## 📚 Documentación Adicional

- **Setup completo:** Ver `SETUP.md`
- **Configuración:** Ver `CONFIG.md`
- **Resumen de implementación:** Ver `ENHANCED_DIAGNOSIS_SUMMARY.md`
- **Guía del frontend:** Ver `FRONTEND_GUIDE.md`

## ✅ Verificación de Funcionamiento

1. ✅ Backend API corriendo en puerto 8000
2. ✅ Frontend corriendo en puerto 3000
3. ✅ PostgreSQL corriendo en puerto 5432
4. ✅ Diagnósticos generados con todos los campos
5. ✅ UI mostrando detalles expandibles

## 🎯 Próximos Pasos Sugeridos

1. Probar con diferentes casos clínicos
2. Evaluar la calidad de los diagnósticos generados
3. Ajustar prompts si es necesario para mejorar outputs
4. Considerar agregar más categorías de información
5. Implementar exportación de reportes en PDF
6. Agregar sistema de feedback para mejorar diagnósticos

---

**¡Listo para usar!** 🚀

Para soporte o preguntas, revisa la documentación en los archivos `.md` del proyecto.
