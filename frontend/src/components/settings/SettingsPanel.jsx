import { useEffect, useState } from 'react'
import { listSettings, bulkUpdateSettings } from '../../api/settings'
import { useApp } from '../../context/AppContext'


const PHASE1_KEYS = ['inactivity_timeout', 'device_domain', 'video_folder']

export default function SettingsPanel() {
  const { reloadSettings } = useApp()
  const [values, setValues]   = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [saved, setSaved]     = useState(false)
  const [error, setError]     = useState(null)

  useEffect(() => {
    listSettings()
      .then(list => {
        const map = {}
        list.forEach(s => { map[s.key] = s.value })
        setValues(map)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const set = (key, val) => setValues(v => ({ ...v, [key]: val }))

  const handleSave = async (keys) => {
    setSaving(true)
    setSaved(false)
    setError(null)
    try {
      const payload = {}
      keys.forEach(k => { payload[k] = values[k] ?? '' })
      await bulkUpdateSettings(payload)
      await reloadSettings()
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="loader">Загрузка настроек…</div>

  return (
    <div style={{ maxWidth: 600 }}>
      {error && (
        <div style={{ color: 'var(--danger)', marginBottom: 16, fontSize: 13 }}>{error}</div>
      )}

      {/* Phase 1 настройки */}
      <div className="card settings-section">
        <div className="settings-section-title">Основные</div>

        <div className="form-group">
          <label className="label">Таймаут неактивности scrcpy (минуты)</label>
          <input
            className="input"
            type="number"
            min={1}
            value={values.inactivity_timeout ?? '10'}
            onChange={e => set('inactivity_timeout', e.target.value)}
            style={{ MozAppearance: 'textfield', appearance: 'textfield' }}
          />
        </div>

        <div className="form-group">
          <label className="label">Домен устройств</label>
          <input
            className="input"
            value={values.device_domain ?? 'http://localhost'}
            onChange={e => set('device_domain', e.target.value)}
            placeholder="http://localhost"
          />
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            Используется для кнопки «Подключиться» в таблице устройств
          </div>
        </div>

        <div className="form-group">
          <label className="label">Папка для видеозаписей</label>
          <input
            className="input mono"
            value={values.video_folder ?? ''}
            onChange={e => set('video_folder', e.target.value)}
            placeholder="C:\Videos или /home/user/videos"
          />
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
            Путь к папке, куда будут сохраняться записи с устройств
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            className="btn btn-primary"
            onClick={() => handleSave(PHASE1_KEYS)}
            disabled={saving}
          >
            {saving ? 'Сохранение…' : 'Сохранить'}
          </button>
          {saved && (
            <span style={{ color: 'var(--success)', fontSize: 13 }}>✓ Сохранено</span>
          )}
        </div>
      </div>

      {/* Phase 2 / Phase 3 заглушки */}
      <div className="card" style={{ opacity: 0.5 }}>
        <div className="settings-section-title">Phase 2 — Парсинг транзакций</div>
        <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          Настройки появятся после реализации Phase 2
        </div>
      </div>

      <div className="card" style={{ opacity: 0.5, marginTop: 14 }}>
        <div className="settings-section-title">Phase 3 — ADB уведомления</div>
        <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          Настройки появятся после реализации Phase 3
        </div>
      </div>
    </div>
  )
}
