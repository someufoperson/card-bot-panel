import { useEffect, useState } from 'react'
import { blockCard, unblockCard, updateCard } from '../../api/cards'
import { useApp } from '../../context/AppContext'
import DeviceSelect from './DeviceSelect'

const TEXT_FIELDS = [
  { key: 'full_name',        label: 'ФИО',                  mono: false },
  { key: 'bank',             label: 'Банк',                  mono: false },
  { key: 'card_number',      label: 'Номер карты',           mono: true  },
  { key: 'phone_number',     label: 'Телефон',               mono: false },
  { key: 'group_name',       label: 'Группа',                mono: false },
  { key: 'responsible_user', label: 'Пользователь',          mono: false },
]

const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—'
const fmtMoney = (v) => v != null
  ? Number(v).toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  : '—'

const makeForm = (card) => ({
  full_name:        card.full_name        ?? '',
  bank:             card.bank             ?? '',
  card_number:      card.card_number      ?? '',
  phone_number:     card.phone_number     ?? '',
  group_name:       card.group_name       ?? '',
  responsible_user: card.responsible_user ?? '',
  balance:          card.balance          != null ? String(card.balance) : '',
  monthly_turnover: card.monthly_turnover != null ? String(card.monthly_turnover) : '',
  folder_link:      card.folder_link      ?? '',
  comment:          card.comment          ?? '',
  device_id:        card.device_id        ? String(card.device_id) : '',
  purchase_date:    card.purchase_date    ? String(card.purchase_date).slice(0, 10) : '',
  pickup_date:      card.pickup_date      ? String(card.pickup_date).slice(0, 10) : '',
})

export default function CardSidebar({ card, onClose, onUpdated }) {
  const open = !!card
  const { settings } = useApp()
  const [copiedLink, setCopiedLink] = useState(false)

  const [editing, setEditing]   = useState(false)
  const [form, setForm]         = useState({})
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState(null)

  const [blockLoading, setBlockLoading] = useState(false)
  const [blockError, setBlockError] = useState(null)

  useEffect(() => {
    if (card) {
      setForm(makeForm(card))
      setEditing(false)
      setError(null)
      setBlockError(null)
    }
  }, [card?.id])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const payload = {}
      TEXT_FIELDS.forEach(({ key }) => {
        const val = form[key].trim()
        payload[key] = val || null
      })
      // numeric fields
      payload.balance          = form.balance          !== '' ? form.balance          : null
      payload.monthly_turnover = form.monthly_turnover !== '' ? form.monthly_turnover : null
      // string fields without trim restriction
      payload.folder_link   = form.folder_link.trim() || null
      payload.comment       = form.comment.trim()     || null
      payload.device_id     = form.device_id          || null
      payload.purchase_date = form.purchase_date      || null
      payload.pickup_date   = form.pickup_date        || null

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
    setForm(makeForm(card))
    setEditing(false)
    setError(null)
  }

  const handleBlock = async () => {
    setBlockLoading(true)
    setBlockError(null)
    try {
      await blockCard(card.id)
      const updated = { ...card, active_block: { blocked_at: new Date().toISOString(), unblocked_at: null } }
      onUpdated?.(updated)
    } catch (e) {
      setBlockError(e.message)
    } finally {
      setBlockLoading(false)
    }
  }

  const handleUnblock = async () => {
    setBlockLoading(true)
    setBlockError(null)
    try {
      await unblockCard(card.id)
      const updated = { ...card, active_block: null }
      onUpdated?.(updated)
    } catch (e) {
      setBlockError(e.message)
    } finally {
      setBlockLoading(false)
    }
  }

  const blocked = !!card?.active_block

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
                  <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
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
                  {TEXT_FIELDS.map(({ key, label, mono }) => (
                    <div className="form-group" key={key}>
                      <label className="label">{label}</label>
                      <input
                        className={`input${mono ? ' mono' : ''}`}
                        value={form[key]}
                        onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                      />
                    </div>
                  ))}

                  <div className="form-row">
                    <div className="form-group">
                      <label className="label">Баланс</label>
                      <input
                        className="input"
                        type="number"
                        step="0.01"
                        value={form.balance}
                        onChange={e => setForm(f => ({ ...f, balance: e.target.value }))}
                        style={{ MozAppearance: 'textfield', appearance: 'textfield' }}
                      />
                    </div>
                    <div className="form-group">
                      <label className="label">Оборот за месяц</label>
                      <input
                        className="input"
                        type="number"
                        step="0.01"
                        value={form.monthly_turnover}
                        onChange={e => setForm(f => ({ ...f, monthly_turnover: e.target.value }))}
                        style={{ MozAppearance: 'textfield', appearance: 'textfield' }}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="label">Ссылка</label>
                    <DeviceSelect
                      value={form.device_id}
                      onChange={v => setForm(f => ({ ...f, device_id: v }))}
                    />
                  </div>

                  <div className="form-group">
                    <label className="label">Комментарий</label>
                    <textarea
                      className="input"
                      value={form.comment}
                      onChange={e => setForm(f => ({ ...f, comment: e.target.value }))}
                      rows={3}
                      style={{ resize: 'vertical' }}
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="label">Дата покупки</label>
                      <input
                        className="input"
                        type="date"
                        value={form.purchase_date}
                        onChange={e => setForm(f => ({ ...f, purchase_date: e.target.value }))}
                        style={{ colorScheme: 'dark' }}
                      />
                    </div>
                    <div className="form-group">
                      <label className="label">Дата забора</label>
                      <input
                        className="input"
                        type="date"
                        value={form.pickup_date}
                        onChange={e => setForm(f => ({ ...f, pickup_date: e.target.value }))}
                        style={{ colorScheme: 'dark' }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                      {saving ? 'Сохранение…' : 'Сохранить'}
                    </button>
                    <button className="btn btn-ghost" onClick={handleCancel} disabled={saving}>
                      Отмена
                    </button>
                  </div>
                </>
              ) : (
                <>
                  {TEXT_FIELDS.map(({ key, label, mono }) => (
                    <div className="detail-row" key={key}>
                      <span className="detail-label">{label}</span>
                      <span className={`detail-value${mono ? ' mono' : ''}`}>
                        {card[key] || '—'}
                      </span>
                    </div>
                  ))}

                  <div className="detail-row">
                    <span className="detail-label">Баланс</span>
                    <span className="detail-value">{fmtMoney(card.balance)}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Оборот за месяц</span>
                    <span className="detail-value">{fmtMoney(card.monthly_turnover)}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Дата покупки</span>
                    <span className="detail-value">{fmtDate(card.purchase_date)}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Дата забора</span>
                    <span className="detail-value">{fmtDate(card.pickup_date)}</span>
                  </div>
                  {card.device && (
                    <div className="detail-row">
                      <span className="detail-label">Ссылка</span>
                      <span className="detail-value" style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <span>
                          {card.device.label || card.device.owner_name || card.device.serial}
                          <span style={{ color: 'var(--text-muted)', marginLeft: 6, fontSize: 11 }}>
                            ({card.device.serial})
                          </span>
                        </span>
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          style={{ padding: '1px 8px', fontSize: 11 }}
                          onClick={() => {
                            const domain = settings.device_domain || 'http://localhost'
                            navigator.clipboard.writeText(`${domain}/${card.device.serial}`)
                            setCopiedLink(true)
                            setTimeout(() => setCopiedLink(false), 2000)
                          }}
                        >
                          {copiedLink ? '✓' : 'Копировать'}
                        </button>
                      </span>
                    </div>
                  )}
                  {card.comment && (
                    <div className="detail-row" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
                      <span className="detail-label">Комментарий</span>
                      <span className="detail-value" style={{ whiteSpace: 'pre-wrap' }}>{card.comment}</span>
                    </div>
                  )}
                </>
              )}

              {/* Block section */}
              <div style={{ marginTop: 24 }}>
                <div style={{
                  fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
                  letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 10,
                }}>
                  Блокировка
                </div>

                {blockError && (
                  <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 8 }}>
                    {blockError}
                  </div>
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '3px 10px', borderRadius: 4, fontSize: 12,
                    background: blocked ? 'var(--danger)' : 'var(--success)',
                    color: '#fff',
                  }}>
                    {blocked ? 'Заблокирована' : 'Активна'}
                  </span>
                  {blocked ? (
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={handleUnblock}
                      disabled={blockLoading}
                    >
                      {blockLoading ? '…' : 'Снять блокировку'}
                    </button>
                  ) : (
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={handleBlock}
                      disabled={blockLoading}
                    >
                      {blockLoading ? '…' : 'Заблокировать'}
                    </button>
                  )}
                </div>

              </div>
            </div>
          </>
        )}
      </aside>
    </>
  )
}
