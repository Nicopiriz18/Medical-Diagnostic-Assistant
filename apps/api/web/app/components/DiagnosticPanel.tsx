import { useState } from 'react';

interface DifferentialDx {
  name: string;
  likelihood: number;
  reasoning: string;
  urgency: "immediate" | "urgent" | "routine";
  general_causes?: string[];
  patient_specific_factors?: string[];
  risk_factors?: string[];
  supporting_findings?: string[];
  contradicting_findings?: string[];
  prognosis?: string;
  complications?: string[];
  recommended_tests?: string[];
  treatment_summary?: string;
}

interface DiagnosticPanelProps {
  assessment: any;
}

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

export default function DiagnosticPanel({ assessment }: DiagnosticPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    differentials: true,
    redFlags: true,
    actionPlan: false,
    soap: false,
    missing: false
  });

  // State for expanded details in each differential diagnosis
  const [expandedDetails, setExpandedDetails] = useState<Record<number, boolean>>({});

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const toggleDetails = (index: number) => {
    setExpandedDetails(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const SectionHeader = ({ title, icon, section }: { title: string; icon: string; section: string }) => (
    <div
      onClick={() => toggleSection(section)}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        cursor: 'pointer',
        padding: '16px 20px',
        background: '#f9fafb',
        borderRadius: '12px 12px 0 0',
        borderBottom: expandedSections[section] ? '1px solid #e5e7eb' : 'none'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 20 }}>{icon}</span>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#111827', margin: 0 }}>{title}</h3>
      </div>
      <span style={{ fontSize: 20, transition: 'transform 0.2s', transform: expandedSections[section] ? 'rotate(180deg)' : 'rotate(0deg)' }}>
        ▼
      </span>
    </div>
  );

  return (
    <div style={{
      background: '#fffbeb',
      borderRadius: 16,
      padding: 24,
      marginTop: 24,
      border: '2px solid #fbbf24',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        marginBottom: 20
      }}>
        <div style={{
          width: 48,
          height: 48,
          borderRadius: '50%',
          background: '#fbbf24',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 24
        }}>
          📋
        </div>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: '#78350f', margin: 0 }}>
            Evaluación Diagnóstica Completa
          </h2>
          <p style={{ fontSize: 14, color: '#92400e', margin: 0 }}>
            Análisis generado por el sistema de agentes
          </p>
        </div>
      </div>

      {/* Resumen del Paciente */}
      <div style={{ 
        background: 'white', 
        borderRadius: 12, 
        padding: 20, 
        marginBottom: 16,
        border: '1px solid #e5e7eb'
      }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: '#2563eb', marginBottom: 8 }}>
          📝 Resumen del Paciente
        </h3>
        <p style={{ color: '#374151', lineHeight: 1.6, margin: 0 }}>{assessment.patient_summary}</p>
      </div>

      {/* Diagnósticos Diferenciales */}
      {assessment.differentials?.length > 0 && (
        <div style={{ background: 'white', borderRadius: 12, marginBottom: 16, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          <SectionHeader title="Diagnósticos Diferenciales" icon="🎯" section="differentials" />
          {expandedSections.differentials && (
            <div style={{ padding: 20 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {assessment.differentials.map((dx: DifferentialDx, idx: number) => (
                  <div key={idx} style={{ 
                    padding: 16, 
                    border: '1px solid #e5e7eb', 
                    borderRadius: 8,
                    background: '#f9fafb'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <h4 style={{ fontSize: 16, fontWeight: 600, color: '#111827', margin: 0, flex: 1 }}>
                        {idx + 1}. {dx.name}
                      </h4>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{ 
                          fontWeight: 700, 
                          color: urgencyColors[dx.urgency as keyof typeof urgencyColors],
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
                    <p style={{ fontSize: 14, color: '#6b7280', lineHeight: 1.6, margin: 0, marginBottom: 12 }}>{dx.reasoning}</p>
                    
                    {/* Expandable Details Button */}
                    <button
                      onClick={() => toggleDetails(idx)}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        background: expandedDetails[idx] ? '#e0e7ff' : '#f3f4f6',
                        border: '1px solid #d1d5db',
                        borderRadius: 6,
                        cursor: 'pointer',
                        fontSize: 13,
                        fontWeight: 600,
                        color: expandedDetails[idx] ? '#3730a3' : '#4b5563',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 6,
                        transition: 'all 0.2s'
                      }}
                    >
                      {expandedDetails[idx] ? '▲ Ocultar detalles' : '▼ Ver detalles completos'}
                    </button>

                    {/* Expanded Details */}
                    {expandedDetails[idx] && (
                      <div style={{ marginTop: 16, padding: 16, background: 'white', borderRadius: 8, border: '1px solid #e5e7eb' }}>
                        
                        {/* Causas */}
                        {(dx.general_causes && dx.general_causes.length > 0) && (
                          <div style={{ marginBottom: 16 }}>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#7c3aed', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              🧬 Causas Generales
                            </h5>
                            <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                              {dx.general_causes.map((cause, i) => (
                                <li key={i} style={{ marginBottom: 4 }}>{cause}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Patient Specific Factors */}
                        {(dx.patient_specific_factors && dx.patient_specific_factors.length > 0) && (
                          <div style={{ marginBottom: 16 }}>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#059669', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              👤 Factores Específicos del Paciente
                            </h5>
                            <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                              {dx.patient_specific_factors.map((factor, i) => (
                                <li key={i} style={{ marginBottom: 4 }}>{factor}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Risk Factors */}
                        {(dx.risk_factors && dx.risk_factors.length > 0) && (
                          <div style={{ marginBottom: 16 }}>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#dc2626', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              ⚠️ Factores de Riesgo
                            </h5>
                            <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                              {dx.risk_factors.map((risk, i) => (
                                <li key={i} style={{ marginBottom: 4 }}>{risk}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Supporting Findings */}
                        {(dx.supporting_findings && dx.supporting_findings.length > 0) && (
                          <div style={{ marginBottom: 16 }}>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#16a34a', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              ✓ Hallazgos que Apoyan
                            </h5>
                            <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                              {dx.supporting_findings.map((finding, i) => (
                                <li key={i} style={{ marginBottom: 4, color: '#166534' }}>{finding}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Contradicting Findings */}
                        {(dx.contradicting_findings && dx.contradicting_findings.length > 0) && (
                          <div style={{ marginBottom: 16 }}>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#ea580c', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              ✗ Hallazgos que Contradicen
                            </h5>
                            <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                              {dx.contradicting_findings.map((finding, i) => (
                                <li key={i} style={{ marginBottom: 4, color: '#9a3412' }}>{finding}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Prognosis */}
                        {dx.prognosis && (
                          <div style={{ marginBottom: 16 }}>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#0891b2', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              📊 Pronóstico
                            </h5>
                            <p style={{ margin: 0, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>{dx.prognosis}</p>
                          </div>
                        )}

                        {/* Complications */}
                        {(dx.complications && dx.complications.length > 0) && (
                          <div style={{ marginBottom: 16 }}>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#dc2626', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              🚨 Complicaciones Potenciales
                            </h5>
                            <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                              {dx.complications.map((comp, i) => (
                                <li key={i} style={{ marginBottom: 4, color: '#7f1d1d' }}>{comp}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Recommended Tests */}
                        {(dx.recommended_tests && dx.recommended_tests.length > 0) && (
                          <div style={{ marginBottom: 16 }}>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#7c3aed', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              🔬 Exámenes Recomendados
                            </h5>
                            <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                              {dx.recommended_tests.map((test, i) => (
                                <li key={i} style={{ marginBottom: 4 }}>{test}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Treatment Summary */}
                        {dx.treatment_summary && (
                          <div>
                            <h5 style={{ fontSize: 13, fontWeight: 700, color: '#059669', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              💊 Opciones de Tratamiento
                            </h5>
                            <p style={{ margin: 0, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>{dx.treatment_summary}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Red Flags */}
      {assessment.red_flags?.length > 0 && (
        <div style={{ background: 'white', borderRadius: 12, marginBottom: 16, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          <SectionHeader title="Señales de Alerta" icon="🚨" section="redFlags" />
          {expandedSections.redFlags && (
            <div style={{ padding: 20 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {assessment.red_flags.map((flag: any, idx: number) => (
                  <div key={idx} style={{ 
                    padding: 16, 
                    borderLeft: `4px solid ${severityColors[flag.severity as keyof typeof severityColors]}`,
                    background: flag.severity === "critical" ? "#fef2f2" : flag.severity === "warning" ? "#fffbeb" : "#eff6ff",
                    borderRadius: 8
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{ 
                        fontSize: 11, 
                        fontWeight: 700, 
                        textTransform: "uppercase",
                        color: severityColors[flag.severity as keyof typeof severityColors]
                      }}>
                        {flag.severity === "critical" ? "🔴 CRÍTICO" : flag.severity === "warning" ? "⚠️ ADVERTENCIA" : "ℹ️ INFO"}
                      </span>
                    </div>
                    <p style={{ fontWeight: 600, color: "#111827", marginBottom: 6, margin: 0 }}>{flag.message}</p>
                    <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>{flag.why_it_matters}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Plan de Acción */}
      {assessment.action_plan?.length > 0 && (
        <div style={{ background: 'white', borderRadius: 12, marginBottom: 16, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          <SectionHeader title="Plan de Acción" icon="✅" section="actionPlan" />
          {expandedSections.actionPlan && (
            <div style={{ padding: 20 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {assessment.action_plan.map((item: any, idx: number) => (
                  <div key={idx} style={{ 
                    padding: 16, 
                    borderLeft: `4px solid ${urgencyColors[item.priority as keyof typeof urgencyColors]}`,
                    background: "#f9fafb",
                    borderRadius: 8
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{ 
                        fontSize: 11, 
                        fontWeight: 700, 
                        textTransform: "uppercase",
                        color: urgencyColors[item.priority as keyof typeof urgencyColors]
                      }}>
                        {item.priority === "immediate" ? "🔴 INMEDIATO" : item.priority === "urgent" ? "🟠 URGENTE" : "🟢 RUTINA"}
                      </span>
                    </div>
                    <p style={{ fontWeight: 600, color: "#111827", marginBottom: 6, margin: 0 }}>{item.action}</p>
                    <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}><em>Justificación:</em> {item.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* SOAP */}
      {assessment.soap && (
        <div style={{ background: 'white', borderRadius: 12, marginBottom: 16, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          <SectionHeader title="Nota SOAP" icon="📝" section="soap" />
          {expandedSections.soap && (
            <div style={{ padding: 20 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <h4 style={{ fontSize: 14, fontWeight: 700, color: '#2563eb', marginBottom: 6, margin: 0 }}>SUBJETIVO</h4>
                  <p style={{ fontSize: 14, color: '#374151', lineHeight: 1.6, margin: 0 }}>{assessment.soap.subjective}</p>
                </div>
                <div>
                  <h4 style={{ fontSize: 14, fontWeight: 700, color: '#2563eb', marginBottom: 6, margin: 0 }}>OBJETIVO</h4>
                  <p style={{ fontSize: 14, color: '#374151', lineHeight: 1.6, margin: 0 }}>{assessment.soap.objective}</p>
                </div>
                <div>
                  <h4 style={{ fontSize: 14, fontWeight: 700, color: '#2563eb', marginBottom: 6, margin: 0 }}>EVALUACIÓN</h4>
                  <p style={{ fontSize: 14, color: '#374151', lineHeight: 1.6, margin: 0 }}>{assessment.soap.assessment}</p>
                </div>
                <div>
                  <h4 style={{ fontSize: 14, fontWeight: 700, color: '#2563eb', marginBottom: 6, margin: 0 }}>PLAN</h4>
                  <p style={{ fontSize: 14, color: '#374151', lineHeight: 1.6, margin: 0 }}>{assessment.soap.plan}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Preguntas Faltantes */}
      {assessment.missing_questions?.length > 0 && (
        <div style={{ background: 'white', borderRadius: 12, marginBottom: 16, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
          <SectionHeader title="Información Adicional Recomendada" icon="❓" section="missing" />
          {expandedSections.missing && (
            <div style={{ padding: 20 }}>
              <ul style={{ paddingLeft: 20, margin: 0 }}>
                {assessment.missing_questions.map((q: string, idx: number) => (
                  <li key={idx} style={{ fontSize: 14, color: '#374151', marginBottom: 8, lineHeight: 1.6 }}>{q}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Limitaciones */}
      {assessment.limitations && (
        <div style={{ 
          background: '#fef2f2', 
          borderRadius: 12, 
          padding: 20,
          border: '2px solid #fca5a5'
        }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: '#991b1b', marginBottom: 8, margin: 0 }}>
            ⚠️ Limitaciones del Análisis
          </h3>
          <p style={{ fontSize: 14, color: '#7f1d1d', lineHeight: 1.6, margin: 0 }}>{assessment.limitations}</p>
        </div>
      )}
    </div>
  );
}
