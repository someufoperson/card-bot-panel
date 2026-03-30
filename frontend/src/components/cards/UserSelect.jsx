import { useEffect, useState } from 'react'
import { listUsernames } from '../../api/users'

export default function UserSelect({ value, onChange, style }) {
  const [usernames, setUsernames] = useState([])

  useEffect(() => {
    listUsernames().then(setUsernames).catch(() => {})
  }, [])

  return (
    <select
      className="input"
      value={value || ''}
      onChange={e => onChange(e.target.value || '')}
      style={style}
    >
      <option value="">— не выбран —</option>
      {usernames.map(u => (
        <option key={u} value={u}>{u}</option>
      ))}
    </select>
  )
}
