const TABS = [
  { id: 'cards',        label: '💳 Карты' },
  { id: 'transactions', label: '📊 Транзакции' },
  { id: 'devices',      label: '📱 Устройства' },
]

export default function Header({ tab, onTabChange }) {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      height: 48,
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border)',
      flexShrink: 0,
    }}>
      <nav style={{ display: 'flex', gap: 2 }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => onTabChange(t.id)}
            style={{
              padding: '6px 14px',
              background: tab === t.id ? 'var(--bg-hover)' : 'transparent',
              border: 'none',
              borderBottom: tab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
              color: tab === t.id ? 'var(--text-primary)' : 'var(--text-muted)',
              fontFamily: 'var(--font-ui)',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'color 0.15s, background 0.15s',
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <button
        onClick={() => onTabChange('settings')}
        style={{
          padding: '6px 12px',
          background: tab === 'settings' ? 'var(--bg-hover)' : 'transparent',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          color: tab === 'settings' ? 'var(--accent)' : 'var(--text-muted)',
          fontFamily: 'var(--font-ui)',
          fontSize: 13,
          cursor: 'pointer',
        }}
      >
        ⚙ Настройки
      </button>
    </header>
  )
}
