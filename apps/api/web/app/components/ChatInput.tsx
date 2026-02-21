import { useState, useRef, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onUploadImage: (file: File) => void;
  disabled?: boolean;
  uploading?: boolean;
}

export default function ChatInput({ onSendMessage, onUploadImage, disabled, uploading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadImage(file);
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div style={{
      position: 'sticky',
      bottom: 0,
      background: 'white',
      padding: '16px',
      borderTop: '1px solid #e5e7eb',
      boxShadow: '0 -2px 10px rgba(0,0,0,0.05)'
    }}>
      <div style={{
        maxWidth: 1200,
        margin: '0 auto',
        display: 'flex',
        gap: 12,
        alignItems: 'flex-end'
      }}>
        {/* Botón de imagen */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || uploading}
          style={{
            padding: '12px',
            borderRadius: '50%',
            border: '1px solid #e5e7eb',
            background: uploading ? '#f3f4f6' : 'white',
            cursor: disabled || uploading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 20,
            transition: 'all 0.2s',
            opacity: disabled || uploading ? 0.5 : 1
          }}
          title="Adjuntar imagen"
        >
          {uploading ? '⏳' : '📎'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />

        {/* Input de texto */}
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={disabled ? "Esperando respuesta..." : "Escribe tu mensaje... (Shift+Enter para nueva línea)"}
          disabled={disabled}
          rows={1}
          style={{
            flex: 1,
            padding: '12px 16px',
            borderRadius: 24,
            border: '1px solid #e5e7eb',
            fontSize: 15,
            fontFamily: 'inherit',
            resize: 'none',
            minHeight: 48,
            maxHeight: 120,
            background: disabled ? '#f9fafb' : 'white',
            color: '#111827',
            outline: 'none'
          }}
          onFocus={(e) => e.target.style.borderColor = '#2563eb'}
          onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
        />

        {/* Botón enviar */}
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          style={{
            padding: '12px 24px',
            borderRadius: 24,
            border: 'none',
            background: disabled || !message.trim() ? '#d1d5db' : '#2563eb',
            color: 'white',
            cursor: disabled || !message.trim() ? 'not-allowed' : 'pointer',
            fontWeight: 600,
            fontSize: 15,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            transition: 'all 0.2s',
            minWidth: 100
          }}
        >
          Enviar 📤
        </button>
      </div>
    </div>
  );
}
