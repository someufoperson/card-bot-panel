import { useEffect, useState } from 'react'
import { listUsers, createUser, deleteUser, resetUserPassword } from '../../api/users'

const ROLE_LABELS = { admin: 'Admin', dev: 'Dev', user: 'User' }
const ROLE_COLORS = {
  admin: 'var(--danger)',
  dev: '#d3869b',
  user: 'var(--text-muted)',
}

export default function UsersTab({ currentUser }) {
  const [users, setUsers]       = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)
  const [newUsername, setNewUsername] = useState('')
  const [newRole, setNewRole]   = useState('user')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState(null)

  const isAdmin = currentUser?.role === 'admin'

  const load = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listUsers()
      setUsers(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!newUsername.trim()) return
    setCreateError(null)
    setCreating(true)
    try {
      await createUser(newUsername.trim(), newRole)
      setNewUsername('')
      setNewRole('user')
      await load()
    } catch (e) {
      setCreateError(e.message)
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (user) => {
    if (!confirm(`Удалить пользователя ${user.username}?`)) return
    try {
      await deleteUser(user.id)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  const handleResetPassword = async (user) => {
    if (!confirm(`Сбросить пароль ${user.username}? Пользователь установит новый при следующем входе.`)) return
    try {
      await resetUserPassword(user.id)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div>
      <h2 style={{ margin: '0 0 20px', fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
        Пользователи
      </h2>

      {isAdmin && (
        <form
          onSubmit={handleCreate}
          style={{
            display: 'flex',
            gap: 8,
            marginBottom: 24,
            alignItems: 'flex-end',
            flexWrap: 'wrap',
          }}
        >
          <div className="form-group" style={{ flex: 1, minWidth: 160, margin: 0 }}>
            <label className="label">Telegram username</label>
            <input
              className="input"
              type="text"
              placeholder="username"
              value={newUsername}
              onChange={e => setNewUsername(e.target.value)}
              disabled={creating}
            />
          </div>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="label">Роль</label>
            <select
              className="input"
              value={newRole}
              onChange={e => setNewRole(e.target.value)}
              disabled={creating}
              style={{ cursor: 'pointer' }}
            >
              <option value="user">User</option>
              <option value="dev">Dev</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button
            className="btn btn-primary"
            type="submit"
            disabled={creating || !newUsername.trim()}
            style={{ height: 36 }}
          >
            {creating ? 'Создание…' : '+ Добавить'}
          </button>
          {createError && (
            <div style={{ width: '100%', fontSize: 13, color: 'var(--danger)' }}>{createError}</div>
          )}
        </form>
      )}

      {loading && <div style={{ color: 'var(--text-muted)', fontSize: 14 }}>Загрузка…</div>}
      {error && <div style={{ color: 'var(--danger)', fontSize: 14 }}>{error}</div>}

      {!loading && !error && (
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          overflow: 'hidden',
        }}>
          {users.length === 0 ? (
            <div style={{ padding: '24px 16px', color: 'var(--text-muted)', fontSize: 14, textAlign: 'center' }}>
              Нет пользователей
            </div>
          ) : (
            users.map((u, i) => (
              <div
                key={u.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 16px',
                  borderBottom: i < users.length - 1 ? '1px solid var(--border)' : 'none',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', flex: 1, fontSize: 14 }}>
                  {u.username}
                  {u.username === currentUser?.username && (
                    <span style={{ marginLeft: 6, fontSize: 11, color: 'var(--text-muted)' }}>(вы)</span>
                  )}
                </span>

                <span style={{
                  fontSize: 11,
                  fontWeight: 700,
                  color: ROLE_COLORS[u.role] || 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  minWidth: 40,
                }}>
                  {ROLE_LABELS[u.role] || u.role}
                </span>

                {u.must_set_password && (
                  <span style={{
                    fontSize: 11,
                    background: 'rgba(250,189,47,0.12)',
                    color: '#fabd2f',
                    border: '1px solid rgba(250,189,47,0.25)',
                    borderRadius: 4,
                    padding: '2px 6px',
                  }}>
                    ожидает пароль
                  </span>
                )}

                {isAdmin && u.username !== currentUser?.username && (
                  <div style={{ display: 'flex', gap: 6 }}>
                    {!u.must_set_password && (
                      <button
                        className="btn"
                        style={{ fontSize: 12, padding: '3px 8px', height: 'auto' }}
                        onClick={() => handleResetPassword(u)}
                        title="Сбросить пароль"
                      >
                        Сброс пароля
                      </button>
                    )}
                    <button
                      className="btn"
                      style={{ fontSize: 12, padding: '3px 8px', height: 'auto', color: 'var(--danger)' }}
                      onClick={() => handleDelete(u)}
                      title="Удалить"
                    >
                      Удалить
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
