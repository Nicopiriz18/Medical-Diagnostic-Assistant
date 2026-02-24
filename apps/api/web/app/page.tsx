"use client";

import { useState, useEffect, useRef } from "react";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import DiagnosticPanel from "./components/DiagnosticPanel";
import ImagePreview from "./components/ImagePreview";

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  images?: string[];
  timestamp: string;
}

export default function Page() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [diagnostic, setDiagnostic] = useState<any>(null);
  const [sessionStatus, setSessionStatus] = useState<'active' | 'completed'>('active');
  const [error, setError] = useState<string | null>(null);
  const [showWelcome, setShowWelcome] = useState(true);
  const [diagnosisProgress, setDiagnosisProgress] = useState<string | null>(null);
  const [isGeneratingDiagnosis, setIsGeneratingDiagnosis] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Auto-scroll to bottom cuando hay nuevos mensajes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, typing]);

  // Crear sesión al montar
  useEffect(() => {
    createSession();
  }, []);

  const createSession = async () => {
    const maxRetries = 3;
    const baseDelayMs = 1000;

    try {
      setLoading(true);
      setError(null);

      let lastError: unknown;
      for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
          const response = await fetch(`${API_URL}/v1/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
          });

          if (!response.ok) {
            throw new Error('Error al crear la sesión');
          }

          const data = await response.json();
          setSessionId(data.id);

          const welcomeMessage: Message = {
            id: 0,
            role: 'assistant',
            content: '👋 ¡Hola! Soy tu asistente médico inteligente.\n\nPuedo ayudarte a:\n• Hacer un análisis clínico detallado\n• Analizar imágenes médicas\n• Generar diagnósticos diferenciales\n\n¿Cuál es tu consulta hoy?',
            timestamp: new Date().toISOString()
          };

          setMessages([welcomeMessage]);
          setShowWelcome(false);
          return;
        } catch (err) {
          lastError = err;
          if (attempt < maxRetries - 1) {
            await new Promise(r => setTimeout(r, baseDelayMs * (attempt + 1)));
          }
        }
      }
      throw lastError;
    } catch (err) {
      setError('No se pudo conectar con el servidor. Verifica que la API esté corriendo.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (content: string) => {
    if (!sessionId) return;

    // Agregar mensaje del usuario
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setTyping(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/v1/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      });

      if (!response.ok) {
        throw new Error('Error al enviar el mensaje');
      }

      const data = await response.json();
      
      // Agregar respuesta del asistente
      const assistantMessage: Message = {
        id: data.id,
        role: 'assistant',
        content: data.content,
        images: data.images,
        timestamp: data.timestamp
      };
      
      setMessages(prev => [...prev, assistantMessage]);

      // Verificar si hay un diagnóstico en el message_metadata
      if (data.message_metadata?.final_diagnosis) {
        // Cargar el diagnóstico
        loadDiagnosis();
      }
    } catch (err) {
      setError('Error al comunicarse con el servidor');
      console.error(err);
    } finally {
      setLoading(false);
      setTyping(false);
    }
  };

  const uploadImage = async (file: File) => {
    if (!sessionId) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_URL}/v1/sessions/${sessionId}/images`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Error al subir la imagen');
      }

      const data = await response.json();
      
      // Agregar mensaje del usuario con la imagen
      const userMessage: Message = {
        id: Date.now(),
        role: 'user',
        content: '📷 Imagen subida',
        images: [data.url],
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, userMessage]);

      // La API responde automáticamente con el análisis
      // Esperar un poco y recargar mensajes
      setTimeout(() => {
        refreshSession();
      }, 1000);

    } catch (err) {
      setError('Error al subir la imagen');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const refreshSession = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${API_URL}/v1/sessions/${sessionId}`);
      
      if (!response.ok) return;

      const data = await response.json();
      
      // Actualizar mensajes con los del servidor
      if (data.messages && data.messages.length > messages.length) {
        const serverMessages = data.messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          images: msg.images,
          timestamp: msg.timestamp
        }));
        setMessages(serverMessages);
      }
    } catch (err) {
      console.error('Error al refrescar la sesión:', err);
    }
  };

  const loadDiagnosis = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${API_URL}/v1/sessions/${sessionId}/diagnosis`);
      
      if (!response.ok) return;

      const data = await response.json();
      setDiagnostic(data.assessment);
      setSessionStatus('completed');
    } catch (err) {
      console.error('Error al cargar diagnóstico:', err);
    }
  };

  const forceDiagnosis = async () => {
    if (!sessionId) return;

    if (!confirm('¿Estás seguro de que quieres finalizar la consulta y obtener el diagnóstico?')) {
      return;
    }

    setIsGeneratingDiagnosis(true);
    setDiagnosisProgress('Iniciando análisis diagnóstico...');
    setError(null);

    try {
      // Use EventSource for Server-Sent Events
      const eventSource = new EventSource(`${API_URL}/v1/sessions/${sessionId}/finalize`);
      
      eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        setDiagnosisProgress(data.message);
      });
      
      eventSource.addEventListener('complete', (event) => {
        const data = JSON.parse(event.data);
        setDiagnostic(data.assessment);
        setSessionStatus('completed');
        setDiagnosisProgress(null);
        setIsGeneratingDiagnosis(false);
        
        // Agregar mensaje del asistente
        const diagMessage: Message = {
          id: Date.now(),
          role: 'assistant',
          content: '📋 He generado la evaluación diagnóstica completa. Revisa el panel a continuación con todos los detalles.',
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, diagMessage]);
        
        eventSource.close();
      });
      
      eventSource.addEventListener('error', (event) => {
        console.error('SSE Error:', event);
        setError('Error al generar el diagnóstico');
        setDiagnosisProgress(null);
        setIsGeneratingDiagnosis(false);
        eventSource.close();
      });

    } catch (err) {
      setError('Error al generar el diagnóstico');
      console.error(err);
      setDiagnosisProgress(null);
      setIsGeneratingDiagnosis(false);
    }
  };

  const startNewSession = () => {
    setMessages([]);
    setDiagnostic(null);
    setSessionStatus('active');
    setError(null);
    setShowWelcome(true);
    createSession();
  };

  const quickActions = [
    "Tengo dolor de cabeza intenso desde hace 2 días",
    "Me duele el pecho cuando respiro profundo",
    "Tengo fiebre alta y dolor de garganta"
  ];

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100vh',
      background: '#f9fafb',
      fontFamily: 'system-ui'
    }}>
      {/* Header */}
      <header style={{
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        padding: '16px 24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h1 style={{ 
              fontSize: 24, 
              fontWeight: 700, 
              color: '#111827',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 12
            }}>
              <span style={{ fontSize: 32 }}>🏥</span>
              Asistente Médico IA
            </h1>
            <p style={{ 
              fontSize: 13, 
              color: '#6b7280', 
              margin: '4px 0 0 0'
            }}>
              Sistema de agentes con RAG e análisis de imágenes
            </p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Estado de sesión */}
            {sessionId && (
              <div style={{
                padding: '6px 12px',
                borderRadius: 16,
                background: sessionStatus === 'active' ? '#dcfce7' : '#dbeafe',
                color: sessionStatus === 'active' ? '#166534' : '#1e40af',
                fontSize: 12,
                fontWeight: 600
              }}>
                {sessionStatus === 'active' ? '🟢 Activa' : '✅ Completada'}
              </div>
            )}
            
            {/* Botón nueva conversación */}
            <button
              onClick={startNewSession}
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                border: '1px solid #e5e7eb',
                background: 'white',
                color: '#374151',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: 14,
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              🔄 Nueva Conversación
            </button>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div style={{
          background: '#fef2f2',
          borderBottom: '1px solid #fca5a5',
          padding: '12px 24px',
          textAlign: 'center'
        }}>
          <p style={{ color: '#dc2626', fontWeight: 600, margin: 0 }}>
            ❌ {error}
          </p>
        </div>
      )}

      {/* Chat Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px',
        paddingBottom: '100px'
      }}>
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          {/* Loading inicial */}
          {loading && messages.length === 0 && (
            <div style={{ 
              textAlign: 'center', 
              padding: '40px',
              color: '#6b7280'
            }}>
              <div style={{
                width: 40,
                height: 40,
                border: '4px solid #e5e7eb',
                borderTopColor: '#2563eb',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 16px'
              }} />
              <p>Iniciando sesión...</p>
            </div>
          )}

          {/* Quick actions (mostrar solo al inicio) */}
          {showWelcome && messages.length <= 1 && sessionId && (
            <div style={{
              background: 'white',
              borderRadius: 12,
              padding: 20,
              marginBottom: 24,
              border: '1px solid #e5e7eb'
            }}>
              <p style={{ fontSize: 14, color: '#6b7280', marginBottom: 12 }}>
                💡 O prueba con una de estas consultas comunes:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {quickActions.map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(action)}
                    disabled={loading}
                    style={{
                      padding: '12px 16px',
                      borderRadius: 8,
                      border: '1px solid #e5e7eb',
                      background: 'white',
                      color: '#374151',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontSize: 14,
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#f9fafb';
                      e.currentTarget.style.borderColor = '#2563eb';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'white';
                      e.currentTarget.style.borderColor = '#e5e7eb';
                    }}
                  >
                    {action}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Mensajes */}
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              role={msg.role}
              content={msg.content}
              images={msg.images}
              timestamp={msg.timestamp}
            />
          ))}

          {/* Typing indicator */}
          {typing && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div style={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                background: '#10b981',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                🏥
              </div>
              <div style={{
                background: 'white',
                padding: '12px 16px',
                borderRadius: 18,
                border: '1px solid #e5e7eb'
              }}>
                <div style={{ display: 'flex', gap: 4 }}>
                  <span style={{ animation: 'bounce 1.4s infinite', animationDelay: '0s' }}>●</span>
                  <span style={{ animation: 'bounce 1.4s infinite', animationDelay: '0.2s' }}>●</span>
                  <span style={{ animation: 'bounce 1.4s infinite', animationDelay: '0.4s' }}>●</span>
                </div>
              </div>
            </div>
          )}

          {/* Botón forzar diagnóstico */}
          {sessionId && messages.length > 2 && sessionStatus === 'active' && !diagnostic && (
            <div style={{
              background: '#eff6ff',
              borderRadius: 12,
              padding: 20,
              marginTop: 24,
              border: '1px solid #bfdbfe',
              textAlign: 'center'
            }}>
              <p style={{ fontSize: 14, color: '#1e40af', marginBottom: 12 }}>
                ¿Ya tienes suficiente información para el diagnóstico?
              </p>
              <button
                onClick={forceDiagnosis}
                disabled={isGeneratingDiagnosis}
                style={{
                  padding: '12px 24px',
                  borderRadius: 8,
                  border: 'none',
                  background: isGeneratingDiagnosis ? '#94a3b8' : '#2563eb',
                  color: 'white',
                  cursor: isGeneratingDiagnosis ? 'not-allowed' : 'pointer',
                  fontWeight: 600,
                  fontSize: 15,
                  opacity: isGeneratingDiagnosis ? 0.7 : 1
                }}
              >
                📋 Generar Diagnóstico Completo
              </button>
            </div>
          )}

          {/* Progress indicator for diagnosis generation */}
          {isGeneratingDiagnosis && diagnosisProgress && (
            <div style={{
              background: 'white',
              borderRadius: 12,
              padding: 24,
              marginTop: 24,
              border: '2px solid #3b82f6',
              boxShadow: '0 4px 6px rgba(59, 130, 246, 0.1)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
                <div style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  border: '4px solid #e0e7ff',
                  borderTopColor: '#3b82f6',
                  animation: 'spin 1s linear infinite'
                }} />
                <div style={{ flex: 1 }}>
                  <h3 style={{ 
                    margin: 0, 
                    fontSize: 16, 
                    fontWeight: 600, 
                    color: '#1e40af',
                    marginBottom: 4
                  }}>
                    🧠 Análisis Clínico en Progreso
                  </h3>
                  <p style={{ 
                    margin: 0, 
                    fontSize: 14, 
                    color: '#6b7280',
                    fontStyle: 'italic'
                  }}>
                    {diagnosisProgress}
                  </p>
                </div>
              </div>
              
              {/* Progress bar */}
              <div style={{
                width: '100%',
                height: 6,
                background: '#e0e7ff',
                borderRadius: 3,
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  background: 'linear-gradient(90deg, #3b82f6, #60a5fa)',
                  animation: 'progressBar 2s ease-in-out infinite',
                  width: '70%'
                }} />
              </div>
              
              <p style={{ 
                fontSize: 12, 
                color: '#9ca3af', 
                marginTop: 12,
                marginBottom: 0,
                textAlign: 'center'
              }}>
                Este proceso puede tomar entre 10-15 segundos...
              </p>
            </div>
          )}

          {/* Panel de diagnóstico */}
          {diagnostic && (
            <DiagnosticPanel assessment={diagnostic} />
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input (fijo abajo) */}
      {sessionId && sessionStatus === 'active' && !diagnostic && (
        <ChatInput
          onSendMessage={sendMessage}
          onUploadImage={uploadImage}
          disabled={loading || typing}
          uploading={uploading}
        />
      )}

      {/* Styles for animations */}
      <style jsx global>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-10px); }
        }
        
        @keyframes progressBar {
          0% { transform: translateX(-100%); }
          50% { transform: translateX(100%); }
          100% { transform: translateX(-100%); }
        }
      `}</style>
    </div>
  );
}
