import { useEffect, useState } from 'react'
import { listCardNames } from '../../api/cards'
import { createDevice, updateDevice, listDevices } from '../../api/devices'

export default function DeviceModal({ device, onClose, onSaved }) {
  const isEdit = !!device?.id

  const [serial,       setSerial]       = useState(device?.serial     ?? '')
  const [label,        setLabel]        = useState(device?.label      ?? '')
  const [ownerName,    setOwnerName]    = useState(device?.owner_name ?? '')
  const [names,        setNames]        = useState([])
  const [unregistered, setUnregistered] = useState([])
  const [saving,       setSaving]       = useState(false)
  const [error,        setError]        = useState(null)

  useEffect(() => {
    listCardNames()
      .then(list => setNames(list))
      .catch(() => {})
    if (!isEdit) {
      listDevices()
        .then(d => {
          const list = d.unregistered ?? []
          setUnregistered(list)
          if (list.length > 0) setSerial(list[0].serial)
        })
        .catch(() => {})
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!label.trim() && !ownerName.trim()) {
      setError('Укажите название или выберите владельца')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const payload = {
        label:      label.trim()     || null,
        owner_name: ownerName.trim() || null,
      }
      if (isEdit) {
        await updateDevice(device.serial, payload)
      } else {
        await createDevice({ serial: serial.trim(), ...payload })
      }
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal modal-animated" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <span>{isEdit ? 'Редактировать устройство' : 'Зарегистрировать устройство'}</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 12 }}>{error}</div>
            )}

            <div className="form-group">
              <label className="label">Serial *</label>
              {isEdit ? (
                <input
                  className="input mono"
                  value={serial}
                  disabled
                />
              ) : unregistered.length === 0 ? (
                <>
                  <input
                    className="input mono"
                    value={serial}
                    onChange={e => setSerial(e.target.value)}
                    placeholder="emulator-5554"
                    required
                  />
                  <div style={{ fontSize: 12, color: 'var(--warning)', marginTop: 5 }}>
                    Устройства не найдены в ADB — возможно, web-scrcpy не запущен. Введите serial вручную.
                  </div>
                </>
              ) : (
                <select
                  className="input mono"
                  value={serial}
                  onChange={e => setSerial(e.target.value)}
                  required
                >
                  {unregistered.map(d => (
                    <option key={d.serial} value={d.serial}>{d.serial}</option>
                  ))}
                </select>
              )}
            </div>

            <div className="form-group">
              <label className="label">Название (label)</label>
              <input
                className="input"
                value={label}
                onChange={e => setLabel(e.target.value)}
                placeholder="Например: Redmi Note 12"
              />
            </div>

            <div className="form-group">
              <label className="label">Владелец</label>
              <select
                className="input"
                value={ownerName}
                onChange={e => setOwnerName(e.target.value)}
              >
                <option value="">— не указан —</option>
                {names.map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
              {names.length === 0 && (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                  Нет карт в базе — сначала добавьте карту
                </div>
              )}
            </div>

            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              Необходимо указать название <em>или</em> выбрать владельца.
            </p>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={saving}>
              Отмена
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? 'Сохранение…' : isEdit ? 'Сохранить' : 'Зарегистрировать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
