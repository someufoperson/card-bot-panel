import { useCallback, useEffect, useState } from 'react'
import { deleteDevice, listDevices, setAccess, setAccessAll } from '../../api/devices'
import { useApp } from '../../context/AppContext'
import { useSSE } from '../../hooks/useSSE'
import AllLogsModal from './AllLogsModal'
import DeviceDetailModal from './DeviceDetailModal'
import DeviceModal from './DeviceModal'

// ── Unified status config ─────────────────────────────────────────────────────
const DOTS = {
  online:       { color: '#27ae60', label: 'Online'      },
  offline:      { color: '#e74c3c', label: 'Offline'     },
  unregistered: { color: '#95a5a6', label: 'ADB'         },
  active:       { color: '#27ae60', label: 'Разрешён'    },
  inactive:     { color: '#e74c3c', label: 'Запрещён'    },
  connected:    { color: '#27ae60', label: 'Активно'     },
  disconnected: { color: '#e74c3c', label: 'Неактивно'   },
}

function Dot({ type }) {
  const s = DOTS[type] ?? DOTS.offline
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span style={{
        width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
        background: s.color,
        boxShadow: `0 0 4px ${s.color}`,
      }} />
      <span style={{ fontSize: 12 }}>{s.label}</span>
    </span>
  )
}

export default function DevicesTab() {
  const { settings } = useApp()
  const [registered,     setRegistered]     = useState([])
  const [unregistered,   setUnregistered]   = useState([])
  const [loading,        setLoading]        = useState(false)
  const [error,          setError]          = useState(null)
  const [deleting,       setDeleting]       = useState(null)
  const [togglingAccess, setTogglingAccess] = useState(null)
  const [registerModal,  setRegisterModal]  = useState(false)
  const [detailDevice,   setDetailDevice]   = useState(null)
  const [copied,         setCopied]         = useState(false)
  const [bulkAccess,     setBulkAccess]     = useState(null)  // 'active' | 'inactive' while loading
  const [showAllLogs,    setShowAllLogs]    = useState(false)

  const load = useCallback(async () => {
    setError(null)
    try {
      const data = await listDevices()
      const reg = data.registered ?? []
      setRegistered(reg)
      setUnregistered(data.unregistered ?? [])
      setDetailDevice(prev =>
        prev ? (reg.find(d => d.serial === prev.serial) ?? prev) : null
      )
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    load().finally(() => setLoading(false))
  }, [load])

  useSSE((e) => { if (e.type === 'devices_updated') load() })

  const handleToggleAccess = async (d, e) => {
    e.stopPropagation()
    const next = d.session_status === 'active' ? 'inactive' : 'active'
    setTogglingAccess(d.serial)
    try { await setAccess(d.serial, next); await load() }
    catch (err) { setError(err.message) }
    finally { setTogglingAccess(null) }
  }

  const handleDelete = async (serial, e) => {
    e.stopPropagation()
    if (!window.confirm(`Удалить устройство ${serial}?`)) return
    setDeleting(serial)
    try { await deleteDevice(serial); await load() }
    catch (err) { setError(err.message) }
    finally { setDeleting(null) }
  }

  const handleCopyLink = (serial, e) => {
    e.stopPropagation()
    const domain = settings.device_domain || 'http://localhost'
    navigator.clipboard.writeText(`${domain}/${serial}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div>
      <div className="toolbar">
        <button className="btn btn-ghost btn-sm" onClick={load}>↻ Обновить</button>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowAllLogs(true)}>
            Логи
          </button>
          <button
            className="btn btn-ghost btn-sm"
            disabled={bulkAccess !== null}
            onClick={async () => {
              setBulkAccess('active')
              try { await setAccessAll('active'); await load() }
              catch (err) { setError(err.message) }
              finally { setBulkAccess(null) }
            }}
          >
            {bulkAccess === 'active' ? '…' : 'Разрешить все'}
          </button>
          <button
            className="btn btn-danger btn-sm"
            disabled={bulkAccess !== null}
            onClick={async () => {
              setBulkAccess('inactive')
              try { await setAccessAll('inactive'); await load() }
              catch (err) { setError(err.message) }
              finally { setBulkAccess(null) }
            }}
          >
            {bulkAccess === 'inactive' ? '…' : 'Запретить все'}
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setRegisterModal(true)}
          >
            + Зарегистрировать
          </button>
        </div>
      </div>

      {error && (
        <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 8 }}>{error}</div>
      )}

      {copied && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 999,
          background: 'var(--success, #27ae60)', color: '#fff',
          padding: '10px 18px', borderRadius: 8, fontSize: 13,
          boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
        }}>
          Ссылка скопирована
        </div>
      )}

      {/* ── Registered devices ──────────────────────────────────────────── */}
      <div className="card" style={{ padding: 0, marginBottom: 20 }}>
        <div style={{
          padding: '10px 16px',
          fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
          letterSpacing: '0.06em', color: 'var(--text-muted)',
          borderBottom: '1px solid var(--border)',
        }}>
          Зарегистрированные устройства
        </div>
        {loading && <div className="loader">Загрузка…</div>}
        {!loading && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Serial</th>
                  <th>Название</th>
                  <th>Владелец</th>
                  <th>Статус</th>
                  <th>Доступ</th>
                  <th>Подключён</th>
                  <th style={{ width: 220 }}></th>
                </tr>
              </thead>
              <tbody>
                {registered.length === 0 ? (
                  <tr>
                    <td colSpan={7}>
                      <div className="empty-state">
                        <div>Нет зарегистрированных устройств</div>
                        <p>Нажмите «Зарегистрировать» чтобы добавить устройство</p>
                      </div>
                    </td>
                  </tr>
                ) : registered.map(d => (
                  <tr
                    key={d.serial}
                    onClick={() => setDetailDevice(d)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td className="td-mono" style={{ fontSize: 12 }}>{d.serial}</td>
                    <td>{d.label || '—'}</td>
                    <td>{d.owner_name || '—'}</td>
                    <td><Dot type={d.status} /></td>
                    <td><Dot type={d.session_status} /></td>
                    <td><Dot type={d.connected ? 'connected' : 'disconnected'} /></td>
                    <td onClick={e => e.stopPropagation()}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={e => handleCopyLink(d.serial, e)}
                        >
                          Скопировать ссылку
                        </button>
                        <button
                          className={`btn btn-sm ${d.session_status === 'active' ? 'btn-danger' : 'btn-ghost'}`}
                          disabled={togglingAccess === d.serial}
                          onClick={e => handleToggleAccess(d, e)}
                        >
                          {togglingAccess === d.serial
                            ? '…'
                            : d.session_status === 'active' ? 'Запретить' : 'Разрешить'}
                        </button>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={e => { e.stopPropagation(); setDetailDevice(d) }}
                        >
                          Изменить
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          disabled={deleting === d.serial}
                          onClick={e => handleDelete(d.serial, e)}
                        >
                          {deleting === d.serial ? '…' : 'Удалить'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showAllLogs && <AllLogsModal onClose={() => setShowAllLogs(false)} />}

      {registerModal && (
        <DeviceModal
          device={null}
          onClose={() => setRegisterModal(false)}
          onSaved={() => { setRegisterModal(false); load() }}
        />
      )}

      {detailDevice && (
        <DeviceDetailModal
          device={detailDevice}
          onClose={() => setDetailDevice(null)}
          onSaved={() => { setDetailDevice(null); load() }}
        />
      )}
    </div>
  )
}
