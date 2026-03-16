import { useEffect, useState } from 'react'
import { updateCard } from '../../api/cards'

const EDITABLE_FIELDS = [
  { key: 'full_name',    label: 'ФИО',          mono: false },
  { key: 'bank',         label: 'Банк',          mono: false },
  { key: 'card_number',  label: 'Номер карты',   mono: true  },
  { key: 'phone_number', label: 'Телефон',       mono: false },
  { key: 'group_name',   label: 'Группа',        mono: false },
]

export default function CardSidebar({ card, onClose, onUpdated }) {
  const open = !!card

  const [editing, setEditing]   = useState(false)
  const [form, setForm]         = useState({})
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState(null)

  useEffect(() => {
    if (card) {
      setForm({
        full_name:    card.full_name    ?? '',
        bank:         card.bank         ?? '',
        card_number:  card.card_number  ?? '',
        phone_number: card.phone_number ?? '',
        group_name:   card.group_name   ?? '',
      })
      setEditing(false)
      setError(null)
    }
  }, [card?.id])

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—'

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const payload = {}
      EDITABLE_FIELDS.forEach(({ key }) => {
        const val = form[key].trim()
        payload[key] = val || null
      })
      const updated = await updateCard(card.id, payload)
      setEditing(false)
      onUpdated?.(updated)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setForm({
      full_name:    card.full_name    ?? '',
      bank:         card.bank         ?? '',
      card_number:  card.card_number  ?? '',
      phone_number: card.phone_number ?? '',
      group_name:   card.group_name   ?? '',
    })
    setEditing(false)
    setError(null)
  }

  return (
    <>
      {open && (
        <div
          onClick={onClose}
          style={{ position: 'fixed', inset: 0, zIndex: 49, background: 'transparent' }}
        />
      )}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        {card && (
          <>
            <div className="sidebar-header">
              <span>Карта</span>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                {!editing && (
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => setEditing(true)}
                  >
                    Изменить
                  </button>
                )}
                <button className="modal-close" onClick={onClose}>×</button>
              </div>
            </div>

            <div className="sidebar-body">
              {error && (
                <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 12 }}>
                  {error}
                </div>
              )}

              {editing ? (
                <>
                  {EDITABLE_FIELDS.map(({ key, label, mono }) => (
                    <div className="form-group" key={key}>
                      <label className="label">{label}</label>
                      <input
                        className={`input${mono ? ' mono' : ''}`}
                        value={form[key]}
                        onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                      />
                    </div>
                  ))}

                  <div className="detail-row">
                    <span className="detail-label">Дата покупки</span>
                    <span className="detail-value">{fmtDate(card.purchase_date)}</span>
                  </div>

                  <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                    <button
                      className="btn btn-primary"
                      onClick={handleSave}
                      disabled={saving}
                    >
                      {saving ? 'Сохранение…' : 'Сохранить'}
                    </button>
                    <button
                      className="btn btn-ghost"
                      onClick={handleCancel}
                      disabled={saving}
                    >
                      Отмена
                    </button>
                  </div>
                </>
              ) : (
                <>
                  {EDITABLE_FIELDS.map(({ key, label, mono }) => (
                    <div className="detail-row" key={key}>
                      <span className="detail-label">{label}</span>
                      <span className={`detail-value${mono ? ' mono' : ''}`}>
                        {card[key] || '—'}
                      </span>
                    </div>
                  ))}
                  <div className="detail-row">
                    <span className="detail-label">Дата покупки</span>
                    <span className="detail-value">{fmtDate(card.purchase_date)}</span>
                  </div>
                </>
              )}

              <div style={{ marginTop: 24 }}>
                <div style={{
                  fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
                  letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 10,
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
