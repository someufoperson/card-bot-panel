import { useEffect, useMemo, useState } from 'react'
import { listDevices } from '../../api/devices'
import { useApp } from '../../context/AppContext'

function tokenize(s) {
  return s.toLowerCase().replace(/[^a-zа-яёa-z0-9]/gi, ' ').split(/\s+/).filter(Boolean)
}

function similarity(hint, deviceLabel) {
  if (!hint || !deviceLabel) return 0
  const hTokens = tokenize(hint)
  const dTokens = tokenize(deviceLabel)
  if (!hTokens.length || !dTokens.length) return 0
  let score = 0
  for (const h of hTokens) {
    for (const d of dTokens) {
      if (h === d) score += 2
      else if (h.length > 2 && d.includes(h)) score += 1
      else if (d.length > 2 && h.includes(d)) score += 1
    }
  }
  return score
}

export default function DeviceSelect({ value, onChange, hint = '', style = {} }) {
  const { settings } = useApp()
  const [devices, setDevices] = useState([])
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    listDevices().then(data => setDevices(data.registered || [])).catch(() => {})
  }, [])

  const label = (d) => d.label || d.owner_name || d.serial

  const sorted = useMemo(() => {
    if (!hint) return devices
    return [...devices].sort((a, b) => similarity(hint, label(b)) - similarity(hint, label(a)))
  }, [devices, hint])

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
        {sorted.map(d => (
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
