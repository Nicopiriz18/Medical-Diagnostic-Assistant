interface ImagePreviewProps {
  url: string;
  analyzing?: boolean;
  onClose?: () => void;
}

export default function ImagePreview({ url, analyzing, onClose }: ImagePreviewProps) {
  return (
    <div style={{
      position: 'relative',
      display: 'inline-block',
      marginTop: 8
    }}>
      <div style={{
        position: 'relative',
        borderRadius: 12,
        overflow: 'hidden',
        border: '2px solid #e5e7eb',
        background: 'white'
      }}>
        <img
          src={url}
          alt="Imagen subida"
          style={{
            maxWidth: '300px',
            maxHeight: '300px',
            display: 'block',
            objectFit: 'contain'
          }}
        />
        
        {analyzing && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: 14,
            fontWeight: 600
          }}>
            <div style={{
              width: 40,
              height: 40,
              border: '4px solid rgba(255,255,255,0.3)',
              borderTopColor: 'white',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              marginBottom: 12
            }} />
            Analizando imagen...
          </div>
        )}
      </div>

      {onClose && !analyzing && (
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: -8,
            right: -8,
            width: 28,
            height: 28,
            borderRadius: '50%',
            border: 'none',
            background: '#ef4444',
            color: 'white',
            cursor: 'pointer',
            fontSize: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }}
          title="Eliminar"
        >
          ×
        </button>
      )}
    </div>
  );
}
