const STYLES = {
  HIGH: {
    background: '#FFEBEE',
    color:      '#C62828',
    border:     '1px solid #EF9A9A',
    dot:        '#C62828',
    label:      'HIGH RISK',
    icon:       '🔴',
  },
  MEDIUM: {
    background: '#FFF8E1',
    color:      '#FF8F00',
    border:     '1px solid #FFE082',
    dot:        '#FF8F00',
    label:      'MEDIUM RISK',
    icon:       '🟡',
  },
  LOW: {
    background: '#E8F5E9',
    color:      '#2E7D32',
    border:     '1px solid #A5D6A7',
    dot:        '#2E7D32',
    label:      'LOW RISK',
    icon:       '🟢',
  },
};

export default function RiskBadge({ level, percent, showPercent = true, size = 'md' }) {
  const style = STYLES[level] || STYLES['LOW'];

  const fontSize   = size === 'sm' ? '11px' : size === 'lg' ? '15px' : '13px';
  const padding    = size === 'sm' ? '3px 8px' : size === 'lg' ? '8px 16px' : '5px 12px';
  const dotSize    = size === 'sm' ? '7px' : size === 'lg' ? '11px' : '9px';

  return (
    <span style={{
      display:        'inline-flex',
      alignItems:     'center',
      gap:            '6px',
      background:     style.background,
      color:          style.color,
      border:         style.border,
      borderRadius:   '999px',
      padding,
      fontSize,
      fontWeight:     '700',
      letterSpacing:  '0.4px',
      fontFamily:     'sans-serif',
    }}>
      {/* Pulsing dot for HIGH risk */}
      <span style={{
        width:          dotSize,
        height:         dotSize,
        borderRadius:   '50%',
        background:     style.dot,
        display:        'inline-block',
        animation:      level === 'HIGH' ? 'pulse 1.4s infinite' : 'none',
        flexShrink:     0,
      }} />

      {style.label}

      {showPercent && percent !== undefined && (
        <span style={{
          background:   style.color,
          color:        'white',
          borderRadius: '999px',
          padding:      '1px 7px',
          fontSize:     `calc(${fontSize} - 1px)`,
        }}>
          {percent}%
        </span>
      )}

      <style>{`
        @keyframes pulse {
          0%   { opacity: 1;   transform: scale(1);    }
          50%  { opacity: 0.4; transform: scale(1.3);  }
          100% { opacity: 1;   transform: scale(1);    }
        }
      `}</style>
    </span>
  );
}