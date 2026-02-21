interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  images?: string[];
  timestamp: string;
}

export default function ChatMessage({ role, content, images, timestamp }: ChatMessageProps) {
  const isUser = role === 'user';
  
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16,
      animation: 'fadeIn 0.3s ease-in'
    }}>
      <div style={{ 
        maxWidth: '70%',
        minWidth: '200px'
      }}>
        {/* Avatar y nombre */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 8,
          marginBottom: 6,
          flexDirection: isUser ? 'row-reverse' : 'row'
        }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: isUser ? '#2563eb' : '#10b981',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 16
          }}>
            {isUser ? '👤' : '🏥'}
          </div>
          <span style={{ 
            fontSize: 12, 
            color: '#6b7280',
            fontWeight: 600
          }}>
            {isUser ? 'Tú' : 'Asistente Médico'}
          </span>
        </div>

        {/* Mensaje */}
        <div style={{
          background: isUser ? '#2563eb' : 'white',
          color: isUser ? 'white' : '#111827',
          padding: '12px 16px',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
          border: isUser ? 'none' : '1px solid #e5e7eb',
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          lineHeight: 1.5
        }}>
          {content}
        </div>

        {/* Imágenes si existen */}
        {images && images.length > 0 && (
          <div style={{ 
            marginTop: 8,
            display: 'flex',
            flexWrap: 'wrap',
            gap: 8
          }}>
            {images.map((img, idx) => (
              <img 
                key={idx}
                src={img}
                alt={`Imagen ${idx + 1}`}
                style={{
                  maxWidth: '200px',
                  maxHeight: '200px',
                  borderRadius: 12,
                  objectFit: 'cover',
                  border: '1px solid #e5e7eb',
                  cursor: 'pointer'
                }}
                onClick={() => window.open(img, '_blank')}
              />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div style={{ 
          fontSize: 11, 
          color: '#9ca3af',
          marginTop: 4,
          textAlign: isUser ? 'right' : 'left'
        }}>
          {formatTime(timestamp)}
        </div>
      </div>
    </div>
  );
}
