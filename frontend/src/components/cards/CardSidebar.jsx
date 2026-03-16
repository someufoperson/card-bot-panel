export default function CardSidebar({ card, onClose }) {
  const open = !!card

  const fmt = (val) => val || '—'
  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—'

  return (
    <>
      {open && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed', inset: 0, zIndex: 49,
            background: 'transparent',
          }}
        />
      )}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        {card && (
          <>
            <div className="sidebar-header">
              <span>Карта</span>
              <button className="modal-close" onClick={onClose}>×</button>
            </div>
            <div className="sidebar-body">
              <div style={{ marginBottom: 20 }}>
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 16,
                  letterSpacing: 2,
                  color: 'var(--accent)',
                  marginBottom: 4,
                }}>
                  {card.card_number_masked}
                </div>
                <div style={{ fontSize: 15, fontWeight: 600 }}>{card.full_name}</div>
                {card.bank && (
                  <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{card.bank}</div>
                )}
              </div>

              <div>
                {[
                  ['Телефон',       fmt(card.phone_number)],
                  ['Дата покупки',  fmtDate(card.purchase_date)],
                  ['Группа',        fmt(card.group_name)],
                  ['Добавлена',     fmtDate(card.created_at)],
                ].map(([label, value]) => (
                  <div className="detail-row" key={label}>
                    <span className="detail-label">{label}</span>
                    <span className="detail-value">{value}</span>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 24 }}>
                <div style={{
                  fontSize: 11,
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: 'var(--text-muted)',
                  marginBottom: 10,
                }}>
                  Транзакции
                </div>
                <div className="empty-state" style={{ padding: '24px 0' }}>
                  <div>Нет транзакций</div>
                  <p>Заполнится в Phase 2</p>
                </div>
              </div>
            </div>
          </>
        )}
      </aside>
    </>
  )
}
