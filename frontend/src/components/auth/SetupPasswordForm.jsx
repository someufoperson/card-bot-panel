import { useState } from 'react'
import { setupPassword } from '../../api/auth'

export default function SetupPasswordForm({ username, onSuccess }) {
  const [password, setPassword]       = useState('')
  const [password2, setPassword2]     = useState('')
  const [showPass, setShowPass]       = useState(false)
  const [error, setError]             = useState(null)
  const [loading, setLoading]         = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (password !== password2) {
      setError('Пароли не совпадают')
      return
    }
    setError(null)
    setLoading(true)
    try {
      await setupPassword(username, password)
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
            Установка пароля
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            Придумайте пароль для <b style={{ color: 'var(--accent)' }}>@{username}</b>
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
          <label className="label">Новый пароль</label>
          <div className="password-wrap">
            <input
              className="input"
              type={showPass ? 'text' : 'password'}
              autoComplete="new-password"
              autoFocus
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

        <div className="form-group">
          <label className="label">Повторите пароль</label>
          <input
            className="input"
            type={showPass ? 'text' : 'password'}
            autoComplete="new-password"
            value={password2}
            onChange={e => setPassword2(e.target.value)}
            disabled={loading}
          />
        </div>

        <button
          className="btn btn-primary"
          type="submit"
          disabled={loading || !password || !password2}
          style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
        >
          {loading ? 'Сохранение…' : 'Сохранить пароль'}
        </button>
      </form>
    </div>
  )
}
