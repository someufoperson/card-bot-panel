import { useEffect, useState } from 'react'
import { listDevices } from '../../api/devices'
import { useApp } from '../../context/AppContext'

export default function DeviceSelect({ value, onChange, style = {} }) {
  const { settings } = useApp()
  const [devices, setDevices] = useState([])
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    listDevices().then(data => setDevices(data.registered || [])).catch(() => {})
  }, [])

  const label = (d) => d.label || d.owner_name || d.serial

  const selected = devices.find(d => d.id === value)

  const handleCopy = () => {
    if (!selected) return
    const domain = settings.device_domain || 'http://localhost'
    navigator.clipboard.writeText(`${domain}/${selected.serial}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
      <select
        className="input"
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ flex: 1, ...style }}
      >
        <option value="">— не выбрано —</option>
        {devices.map(d => (
          <option key={d.id} value={d.id}>
            {label(d)} ({d.serial})
          </option>
        ))}
      </select>
      {selected && (
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={handleCopy}
          title="Скопировать ссылку"
          style={{ flexShrink: 0, whiteSpace: 'nowrap' }}
        >
          {copied ? '✓' : 'Копировать'}
        </button>
      )}
    </div>
  )
}
