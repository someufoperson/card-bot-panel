import { useState } from 'react'
import { login } from '../../api/auth'

export default function LoginForm({ onSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError]       = useState(null)
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(username, password)
      onSuccess()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <form
        onSubmit={handleSubmit}
        style={{
          width: 340,
          background: 'linear-gradient(180deg, #3A3633 0%, #32302F 100%)',
          border: '1px solid #504945',
          borderBottomColor: 'var(--border)',
          borderRadius: 'var(--radius)',
          padding: 32,
          boxShadow: 'var(--shadow-lg), 0 0 0 1px rgba(235,219,178,0.04)',
        }}
      >
        <div style={{ marginBottom: 28, textAlign: 'center' }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Card Panel
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            Введите данные для входа
          </div>
        </div>

        {error && (
          <div style={{
            background: 'rgba(251,73,52,0.1)',
            border: '1px solid rgba(251,73,52,0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '8px 12px',
            fontSize: 13,
            color: 'var(--danger)',
            marginBottom: 16,
          }}>
            {error}
          </div>
        )}

        <div className="form-group">
          <label className="label">Логин</label>
          <input
            className="input"
            type="text"
            autoComplete="username"
            autoFocus
            value={username}
            onChange={e => setUsername(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="label">Пароль</label>
          <div className="password-wrap">
            <input
              className="input"
              type={showPass ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              disabled={loading}
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPass(v => !v)}
              tabIndex={-1}
            >
              {showPass ? '🙈' : '👁'}
            </button>
          </div>
        </div>

        <button
          className="btn btn-primary"
          type="submit"
          disabled={loading || !username || !password}
          style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
        >
          {loading ? 'Вход…' : 'Войти'}
        </button>
      </form>
    </div>
  )
}
