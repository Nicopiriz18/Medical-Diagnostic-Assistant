"use client";

import { useState } from "react";

const urgencyColors = {
  immediate: "#dc2626",
  urgent: "#ea580c",
  routine: "#16a34a"
};

const severityColors = {
  critical: "#dc2626",
  warning: "#f59e0b",
  info: "#3b82f6"
};

export default function Page() {
  const [caseText, setCaseText] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setErr(null);
    setData(null);
    try {
      const r = await fetch(process.env.NEXT_PUBLIC_API_URL + "/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_text: caseText })
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j?.detail || "Error");
      setData(j);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  const assessment = data?.assessment;

  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: 24, fontFamily: "system-ui", background: "#f9fafb", minHeight: "100vh" }}>
      <div style={{ background: "white", borderRadius: 12, padding: 32, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
        <h1 style={{ fontSize: 32, fontWeight: 700, color: "#111827", marginBottom: 8 }}>
          🏥 Medical Diagnostic Assistant
        </h1>
        <p style={{ color: "#6b7280", fontSize: 15 }}>
          Demo educativa de apoyo al razonamiento clínico. No reemplaza juicio médico profesional.
        </p>

        <textarea
          value={caseText}
          onChange={(e) => setCaseText(e.target.value)}
          placeholder="Ingrese el caso clínico completo: síntomas, signos vitales, exámenes, antecedentes..."
          rows={8}
          style={{ 
            width: "100%", 
            padding: 16, 
            marginTop: 20, 
            borderRadius: 8, 
            border: "1px solid #e5e7eb",
            fontSize: 15,
            fontFamily: "inherit",
            resize: "vertical"
          }}
        />

        <button
          onClick={run}
          disabled={loading || caseText.trim().length < 10}
          style={{ 
            marginTop: 16, 
            padding: "12px 24px", 
            borderRadius: 8, 
            cursor: loading ? "wait" : "pointer",
            background: loading || caseText.trim().length < 10 ? "#d1d5db" : "#2563eb",
            color: "white",
            border: "none",
            fontWeight: 600,
            fontSize: 15
          }}
        >
          {loading ? "⏳ Analizando..." : "🔍 Analizar Caso"}
        </button>

        {err && (
          <div style={{ marginTop: 16, padding: 16, background: "#fef2f2", borderLeft: "4px solid #dc2626", borderRadius: 8 }}>
            <p style={{ color: "#dc2626", fontWeight: 600 }}>❌ Error: {err}</p>
          </div>
        )}
      </div>

      {assessment && (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Resumen del Paciente */}
          <section style={{ background: "white", borderRadius: 12, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: "#111827", marginBottom: 12 }}>📋 Resumen del Paciente</h2>
            <p style={{ color: "#374151", lineHeight: 1.6 }}>{assessment.patient_summary}</p>
          </section>

          {/* Red Flags */}
          {assessment.red_flags?.length > 0 && (
            <section style={{ background: "white", borderRadius: 12, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: "#111827", marginBottom: 16 }}>🚨 Señales de Alerta</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {assessment.red_flags.map((flag: any, idx: number) => (
                  <div key={idx} style={{ 
                    padding: 16, 
                    borderLeft: `4px solid ${severityColors[flag.severity]}`,
                    background: flag.severity === "critical" ? "#fef2f2" : flag.severity === "warning" ? "#fffbeb" : "#eff6ff",
                    borderRadius: 8
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                      <span style={{ 
                        fontSize: 11, 
                        fontWeight: 700, 
                        textTransform: "uppercase",
                        color: severityColors[flag.severity]
                      }}>
                        {flag.severity === "critical" ? "🔴 CRÍTICO" : flag.severity === "warning" ? "⚠️ ADVERTENCIA" : "ℹ️ INFO"}
                      </span>
                    </div>
                    <p style={{ fontWeight: 600, color: "#111827", marginBottom: 6 }}>{flag.message}</p>
                    <p style={{ fontSize: 14, color: "#6b7280" }}>{flag.why_it_matters}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Diagnósticos Diferenciales */}
          {assessment.differentials?.length > 0 && (
            <section style={{ background: "white", borderRadius: 12, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: "#111827", marginBottom: 16 }}>🎯 Diagnósticos Diferenciales</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {assessment.differentials.map((dx: any, idx: number) => (
                  <div key={idx} style={{ padding: 16, border: "1px solid #e5e7eb", borderRadius: 8 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <h3 style={{ fontSize: 16, fontWeight: 600, color: "#111827", flex: 1 }}>{dx.name}</h3>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ 
                          fontWeight: 700, 
                          color: urgencyColors[dx.urgency],
                          padding: "4px 8px",
                          background: dx.urgency === "immediate" ? "#fef2f2" : dx.urgency === "urgent" ? "#fff7ed" : "#f0fdf4",
                          borderRadius: 6,
                          textTransform: "uppercase",
                          fontSize: 11
                        }}>
                          {dx.urgency === "immediate" ? "INMEDIATO" : dx.urgency === "urgent" ? "URGENTE" : "RUTINA"}
                        </span>
                        <span style={{ fontSize: 18, fontWeight: 700, color: "#2563eb" }}>{dx.likelihood}%</span>
                      </div>
                    </div>
                    <p style={{ fontSize: 14, color: "#6b7280", lineHeight: 1.6 }}>{dx.reasoning}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Plan de Acción */}
          {assessment.action_plan?.length > 0 && (
            <section style={{ background: "white", borderRadius: 12, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: "#111827", marginBottom: 16 }}>✅ Plan de Acción</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {assessment.action_plan.map((item: any, idx: number) => (
                  <div key={idx} style={{ 
                    padding: 16, 
                    borderLeft: `4px solid ${urgencyColors[item.priority]}`,
                    background: "#f9fafb",
                    borderRadius: 8
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                      <span style={{ 
                        fontSize: 11, 
                        fontWeight: 700, 
                        textTransform: "uppercase",
                        color: urgencyColors[item.priority]
                      }}>
                        {item.priority === "immediate" ? "🔴 INMEDIATO" : item.priority === "urgent" ? "🟠 URGENTE" : "🟢 RUTINA"}
                      </span>
                    </div>
                    <p style={{ fontWeight: 600, color: "#111827", marginBottom: 6 }}>{item.action}</p>
                    <p style={{ fontSize: 14, color: "#6b7280" }}><em>Justificación:</em> {item.rationale}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* SOAP */}
          {assessment.soap && (
            <section style={{ background: "white", borderRadius: 12, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: "#111827", marginBottom: 16 }}>📝 Nota SOAP</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#2563eb", marginBottom: 6 }}>SUBJETIVO</h3>
                  <p style={{ fontSize: 14, color: "#374151", lineHeight: 1.6 }}>{assessment.soap.subjective}</p>
                </div>
                <div>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#2563eb", marginBottom: 6 }}>OBJETIVO</h3>
                  <p style={{ fontSize: 14, color: "#374151", lineHeight: 1.6 }}>{assessment.soap.objective}</p>
                </div>
                <div>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#2563eb", marginBottom: 6 }}>EVALUACIÓN</h3>
                  <p style={{ fontSize: 14, color: "#374151", lineHeight: 1.6 }}>{assessment.soap.assessment}</p>
                </div>
                <div>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: "#2563eb", marginBottom: 6 }}>PLAN</h3>
                  <p style={{ fontSize: 14, color: "#374151", lineHeight: 1.6 }}>{assessment.soap.plan}</p>
                </div>
              </div>
            </section>
          )}

          {/* Preguntas Faltantes */}
          {assessment.missing_questions?.length > 0 && (
            <section style={{ background: "white", borderRadius: 12, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: "#111827", marginBottom: 16 }}>❓ Información Adicional Recomendada</h2>
              <ul style={{ paddingLeft: 20, margin: 0 }}>
                {assessment.missing_questions.map((q: string, idx: number) => (
                  <li key={idx} style={{ fontSize: 14, color: "#374151", marginBottom: 8, lineHeight: 1.6 }}>{q}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Limitaciones */}
          {assessment.limitations && (
            <section style={{ background: "#fffbeb", borderRadius: 12, padding: 24, border: "1px solid #fcd34d" }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: "#92400e", marginBottom: 8 }}>⚠️ Limitaciones del Análisis</h2>
              <p style={{ fontSize: 14, color: "#78350f", lineHeight: 1.6 }}>{assessment.limitations}</p>
            </section>
          )}
        </div>
      )}
    </main>
  );
}
