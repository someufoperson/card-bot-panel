import { useEffect, useState } from 'react'
import { blockCard, deleteCard, unblockCard, updateCard } from '../../api/cards'
import DeviceSelect from './DeviceSelect'

const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—'

const G = ({ label, children, half }) => (
  <div style={{ marginBottom: 10, ...(half ? {} : {}) }}>
    <label style={{ display: 'block', fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
      {label}
    </label>
    {children}
  </div>
)

const Row = ({ children }) => (
  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 0 }}>
    {children}
  </div>
)

export default function CardEditModal({ card, onClose, onUpdated, onDeleted }) {
  const [form, setForm]     = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState(null)

  const [blockLoading, setBlockLoading] = useState(false)
  const [blockError, setBlockError]     = useState(null)

  useEffect(() => {
    setForm({
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
    setError(null)
    setBlockError(null)
  }, [card.id]) // eslint-disable-line

  const set = (key, value) => setForm(f => ({ ...f, [key]: value }))

  const inp = (key, opts = {}) => (
    <input
      className={`input${opts.mono ? ' mono' : ''}`}
      style={{ padding: '6px 10px', fontSize: 13 }}
      type={opts.type || 'text'}
      step={opts.type === 'number' ? '0.01' : undefined}
      value={form[key] ?? ''}
      onChange={e => set(key, e.target.value)}
      placeholder={opts.placeholder}
      readOnly={opts.readOnly}
    />
  )

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const payload = {
        full_name:        form.full_name.trim()        || null,
        bank:             form.bank.trim()             || null,
        card_number:      form.card_number.trim()      || null,
        phone_number:     form.phone_number.trim()     || null,
        group_name:       form.group_name.trim()       || null,
        responsible_user: form.responsible_user.trim() || null,
        balance:          form.balance !== ''          ? form.balance          : null,
        monthly_turnover: form.monthly_turnover !== '' ? form.monthly_turnover : null,
        folder_link:      form.folder_link.trim()      || null,
        comment:          form.comment.trim()          || null,
        device_id:        form.device_id               || null,
        purchase_date:    form.purchase_date           || null,
        pickup_date:      form.pickup_date             || null,
      }
      const updated = await updateCard(card.id, payload)
      onUpdated?.(updated)
      onClose()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
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

  const handleDelete = async () => {
    if (!window.confirm(`Удалить карту ${card.full_name}?`)) return
    try {
      await deleteCard(card.id)
      onDeleted?.()
      onClose()
    } catch (e) {
      setError(e.message)
    }
  }

  const blocked = !!card.active_block

  return (
    <div className="overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div
        className="modal-animated"
        style={{
          background: 'linear-gradient(180deg, #3A3633 0%, #32302F 100%)',
          border: '1px solid #504945',
          borderRadius: 'var(--radius)',
          boxShadow: 'var(--shadow-lg), 0 0 0 1px rgba(235,219,178,0.04)',
          width: 560,
          maxWidth: '95vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 20px',
          borderBottom: '1px solid var(--bg-hover)',
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 16, fontWeight: 600 }}>Редактировать карту</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '14px 20px' }}>
          {error && (
            <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 10 }}>{error}</div>
          )}

          <G label="ФИО">{inp('full_name')}</G>

          <Row>
            <G label="Банк">{inp('bank')}</G>
            <G label="Группа">{inp('group_name')}</G>
          </Row>

          <Row>
            <G label="Номер карты">{inp('card_number', { mono: true })}</G>
            <G label="Телефон">{inp('phone_number', { placeholder: '+79001234567' })}</G>
          </Row>

          <Row>
            <G label="Баланс">{inp('balance', { type: 'number' })}</G>
            <G label="Оборот за месяц">{inp('monthly_turnover', { type: 'number' })}</G>
          </Row>

          <Row>
            <G label="Пользователь">{inp('responsible_user')}</G>
            <G label="Ссылка">
              <DeviceSelect
                value={form.device_id ?? ''}
                onChange={v => set('device_id', v)}
                style={{ padding: '6px 10px', fontSize: 13 }}
              />
            </G>
          </Row>

          <Row>
            <G label="Дата покупки">
              <input
                className="input"
                style={{ padding: '6px 10px', fontSize: 13, colorScheme: 'dark' }}
                type="date"
                value={form.purchase_date ?? ''}
                onChange={e => set('purchase_date', e.target.value)}
              />
            </G>
            <G label="Дата забора">
              <input
                className="input"
                style={{ padding: '6px 10px', fontSize: 13, colorScheme: 'dark' }}
                type="date"
                value={form.pickup_date ?? ''}
                onChange={e => set('pickup_date', e.target.value)}
              />
            </G>
          </Row>

          <G label="Комментарий">
            <textarea
              className="input"
              style={{ padding: '6px 10px', fontSize: 13, resize: 'vertical' }}
              value={form.comment ?? ''}
              onChange={e => set('comment', e.target.value)}
              rows={2}
            />
          </G>

          {/* Block section */}
          <div style={{ borderTop: '1px solid var(--bg-hover)', marginTop: 6, paddingTop: 12 }}>
            <div style={{
              fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
              letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 8,
            }}>
              Блокировка
            </div>

            {blockError && (
              <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 6 }}>{blockError}</div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
              <span style={{
                padding: '2px 10px', borderRadius: 4, fontSize: 12,
                background: blocked ? 'var(--danger)' : 'var(--bg-hover)',
                color: blocked ? '#fff' : 'var(--text-muted)',
              }}>
                {blocked ? 'Заблокирована' : 'Отсутствует'}
              </span>
              {blocked ? (
                <button className="btn btn-ghost btn-sm" onClick={handleUnblock} disabled={blockLoading}>
                  {blockLoading ? '…' : 'Снять блокировку'}
                </button>
              ) : (
                <button className="btn btn-danger btn-sm" onClick={handleBlock} disabled={blockLoading}>
                  {blockLoading ? '…' : 'Заблокировать'}
                </button>
              )}
            </div>

          </div>
        </div>

        {/* Footer */}
        <div style={{
          display: 'flex', justifyContent: 'flex-end', gap: 8,
          padding: '12px 20px',
          borderTop: '1px solid var(--bg-hover)',
          background: 'rgba(0,0,0,0.15)',
          flexShrink: 0,
          borderRadius: '0 0 var(--radius) var(--radius)',
        }}>
          <button className="btn btn-danger" onClick={handleDelete} disabled={saving}>Удалить</button>
          <div style={{ flex: 1 }} />
          <button className="btn btn-ghost" onClick={onClose} disabled={saving}>Отмена</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Сохранение…' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  )
}
