const TABS = [
  {
    id: 'cards',
    label: 'Карты',
    icon: (
      <svg width="22" height="22" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="2" y="4" width="16" height="12" rx="2" stroke="currentColor" strokeWidth="1.5"/>
        <rect x="2" y="7.5" width="16" height="2.5" fill="currentColor" opacity="0.35"/>
        <rect x="4" y="12" width="4" height="1.5" rx="0.5" fill="currentColor"/>
        <rect x="9.5" y="12" width="2.5" height="1.5" rx="0.5" fill="currentColor"/>
      </svg>
    ),
  },
  {
    id: 'transactions',
    label: 'Транзакции',
    icon: (
      <svg width="22" height="22" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="3" y="13" width="2.5" height="4" rx="0.5" fill="currentColor"/>
        <rect x="7.5" y="9" width="2.5" height="8" rx="0.5" fill="currentColor"/>
        <rect x="12" y="6" width="2.5" height="11" rx="0.5" fill="currentColor"/>
        <path d="M4 9L8.5 6L13 3.5L17 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx="17" cy="2" r="1.2" fill="currentColor"/>
      </svg>
    ),
  },
  {
    id: 'devices',
    label: 'Устройства',
    icon: (
      <svg width="22" height="22" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="6" y="1.5" width="8" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.5"/>
        <circle cx="10" cy="13.5" r="1" fill="currentColor"/>
        <line x1="8" y1="4" x2="12" y2="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M3.5 8H6M14 8H16.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
        <path d="M3 11L5 11M15 11L17 11" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity="0.5"/>
      </svg>
    ),
  },
  {
    id: 'settings',
    label: 'Настройки',
    icon: (
      <svg width="22" height="22" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.5"/>
        <path
          d="M10 2v1.5M10 16.5V18M2 10h1.5M16.5 10H18M3.93 3.93l1.06 1.06M15.01 15.01l1.06 1.06M3.93 16.07l1.06-1.06M15.01 4.99l1.06-1.06"
          stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
        />
      </svg>
    ),
  },
]

export default function LeftBar({ tab, onTabChange }) {
  return (
    <aside style={{
      width: 48,
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border)',
      boxShadow: '2px 0 12px rgba(0,0,0,0.25)',
      paddingTop: 10,
      paddingBottom: 10,
      userSelect: 'none',
      gap: 2,
    }}>
      {TABS.map(t => {
        const active = tab === t.id
        return (
          <div key={t.id} style={{ position: 'relative' }}>
            {/* Активный индикатор — полоска слева */}
            {active && (
              <span style={{
                position: 'absolute',
                left: 0, top: 6, bottom: 6,
                width: 3,
                borderRadius: '0 2px 2px 0',
                background: 'var(--accent)',
              }} />
            )}
            <button
              onClick={() => onTabChange(t.id)}
              title={t.label}
              style={{
                width: 44,
                height: 44,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: active
                  ? 'linear-gradient(135deg, rgba(131,165,152,0.15) 0%, rgba(131,165,152,0.07) 100%)'
                  : 'transparent',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                color: active ? 'var(--accent)' : 'var(--text-muted)',
                transition: 'color 0.15s, background 0.15s',
                padding: 0,
              }}
              onMouseEnter={e => {
                if (!active) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.05)'
                  e.currentTarget.style.color = 'var(--text-primary)'
                }
              }}
              onMouseLeave={e => {
                if (!active) {
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.color = 'var(--text-muted)'
                }
              }}
            >
              {t.icon}
            </button>
          </div>
        )
      })}
    </aside>
  )
}
