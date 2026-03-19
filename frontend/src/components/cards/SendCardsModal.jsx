import { useEffect, useState } from 'react'
import { listGroups } from '../../api/groups'
import { sendCards } from '../../api/cards'

export default function SendCardsModal({ selectedIds, onClose }) {
  const [groups, setGroups]     = useState([])
  const [chatId, setChatId]     = useState('')
  const [sending, setSending]   = useState(false)
  const [error, setError]       = useState(null)

  useEffect(() => {
    listGroups().then(setGroups).catch(() => {})
  }, [])

  const handleSend = async () => {
    if (!chatId) return
    setSending(true)
    setError(null)
    try {
      await sendCards([...selectedIds], chatId)
      onClose()
    } catch (e) {
      setError(e.message)
      setSending(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
        <div className="modal-header">
          <span>Отправить карты</span>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
            Выбрано карт: <strong>{selectedIds.size}</strong>
          </p>

          <div className="form-group">
            <label className="label">Группа получателя</label>
            <select
              className="input"
              value={chatId}
              onChange={e => setChatId(e.target.value)}
            >
              <option value="">— Выберите группу —</option>
              {groups.map(g => (
                <option key={g.id} value={g.name}>
                  {g.name} ({g.type === 'donor' ? 'донор' : 'выдача'})
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div style={{ color: 'var(--danger)', fontSize: 13, marginTop: 8 }}>{error}</div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Отмена</button>
          <button
            className="btn btn-primary"
            disabled={!chatId || sending}
            onClick={handleSend}
          >
            {sending ? 'Отправка…' : 'Отправить'}
          </button>
        </div>
      </div>
    </div>
  )
}
