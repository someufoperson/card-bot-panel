import { useState } from 'react'
import { createCard } from '../../api/cards'
import DeviceSelect from './DeviceSelect'

const EMPTY = {
  full_name: '', bank: '', card_number: '', phone_number: '',
  device_id: '', purchase_date: '', pickup_date: '', group_name: '',
  balance: '0', monthly_turnover: '0', responsible_user: '',
  folder_link: '', comment: '',
}

function validate(form) {
  const errs = {}
  if (!form.full_name.trim()) errs.full_name = 'Обязательное поле'
  const digits = form.card_number.replace(/\D/g, '')
  if (digits.length !== 16) errs.card_number = 'Номер карты должен содержать 16 цифр'
  if (form.phone_number && !/^\+7\d{10}$/.test(form.phone_number))
    errs.phone_number = 'Формат: +7XXXXXXXXXX'
  return errs
}

export default function CardModal({ onClose, onCreated }) {
  const [form, setForm]       = useState(EMPTY)
  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)

  const set = (field, value) => {
    setForm(f => ({ ...f, [field]: value }))
    setErrors(e => ({ ...e, [field]: undefined }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate(form)
    if (Object.keys(errs).length) { setErrors(errs); return }

    setLoading(true)
    try {
      const payload = { ...form }
      if (!payload.bank)             delete payload.bank
      if (!payload.phone_number)     delete payload.phone_number
      if (!payload.purchase_date)    delete payload.purchase_date
      if (!payload.device_id)        delete payload.device_id
      if (!payload.pickup_date)      delete payload.pickup_date
      if (!payload.group_name)       delete payload.group_name
      if (!payload.balance)          delete payload.balance
      if (!payload.monthly_turnover) delete payload.monthly_turnover
      if (!payload.responsible_user) delete payload.responsible_user
      if (!payload.folder_link)      delete payload.folder_link
      if (!payload.comment)          delete payload.comment

      await createCard(payload)
      onCreated()
      onClose()
    } catch (err) {
      setErrors({ _global: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">Добавить карту</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          {errors._global && (
            <div style={{ color: 'var(--danger)', marginBottom: 12, fontSize: 13 }}>
              {errors._global}
            </div>
          )}

          <div className="form-group">
            <label className="label">ФИО *</label>
            <input
              className={`input ${errors.full_name ? 'input-error' : ''}`}
              value={form.full_name}
              onChange={e => set('full_name', e.target.value)}
              placeholder="Иванов Иван Иванович"
            />
            {errors.full_name && <div className="error-msg">{errors.full_name}</div>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="label">Банк</label>
              <input
                className="input"
                value={form.bank}
                onChange={e => set('bank', e.target.value)}
                placeholder="Сбербанк"
              />
            </div>
            <div className="form-group">
              <label className="label">Группа</label>
              <input
                className="input"
                value={form.group_name}
                onChange={e => set('group_name', e.target.value)}
                placeholder="—"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="label">Ссылка</label>
            <DeviceSelect value={form.device_id} onChange={v => set('device_id', v)} hint={[form.full_name, form.folder_link].filter(Boolean).join(' ')} />
          </div>

          <div className="form-group">
            <label className="label">Номер карты * (16 цифр)</label>
            <input
              className={`input mono ${errors.card_number ? 'input-error' : ''}`}
              value={form.card_number}
              onChange={e => set('card_number', e.target.value.replace(/\s/g, ''))}
              placeholder="1234567890123456"
              maxLength={19}
            />
            {errors.card_number && <div className="error-msg">{errors.card_number}</div>}
          </div>

          <div className="form-group">
            <label className="label">Телефон</label>
            <input
              className={`input ${errors.phone_number ? 'input-error' : ''}`}
              value={form.phone_number}
              onChange={e => set('phone_number', e.target.value)}
              placeholder="+79001234567"
            />
            {errors.phone_number && <div className="error-msg">{errors.phone_number}</div>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="label">Дата покупки</label>
              <input
                className="input"
                type="date"
                value={form.purchase_date}
                onChange={e => set('purchase_date', e.target.value)}
                style={{ colorScheme: 'dark' }}
              />
            </div>
            <div className="form-group">
              <label className="label">Дата забора</label>
              <input
                className="input"
                type="date"
                value={form.pickup_date}
                onChange={e => set('pickup_date', e.target.value)}
                style={{ colorScheme: 'dark' }}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="label">Баланс</label>
              <input
                className="input"
                type="number"
                step="0.01"
                value={form.balance}
                onChange={e => set('balance', e.target.value)}
                placeholder="0.00"
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
                onChange={e => set('monthly_turnover', e.target.value)}
                placeholder="0.00"
                style={{ MozAppearance: 'textfield', appearance: 'textfield' }}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="label">Пользователь (ответственный)</label>
            <input
              className="input"
              value={form.responsible_user}
              onChange={e => set('responsible_user', e.target.value)}
              placeholder="Имя пользователя"
            />
          </div>

          <div className="form-group">
            <label className="label">Комментарий</label>
            <textarea
              className="input"
              value={form.comment}
              onChange={e => set('comment', e.target.value)}
              placeholder="Произвольный комментарий"
              rows={2}
              style={{ resize: 'vertical' }}
            />
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Отмена
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Сохранение…' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
