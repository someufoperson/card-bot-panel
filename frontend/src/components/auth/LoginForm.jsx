import { useState } from 'react'
import { login } from '../../api/auth'

export default function LoginForm({ onSuccess, onMustSetPassword }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [step, setStep]         = useState('username') // 'username' | 'password'
  const [error, setError]       = useState(null)
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const result = await login(username, step === 'password' ? password : null)
      if (result.must_set_password) {
        onMustSetPassword(username)
      } else {
        onSuccess()
      }
    } catch (err) {
      if (step === 'username') {
        // пользователь существует, но нужен пароль — переходим к шагу пароля
        setStep('password')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleBack = () => {
    setStep('username')
    setPassword('')
    setError(null)
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
            {step === 'username' ? 'Введите логин для входа' : `Введите пароль для ${username}`}
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

        {step === 'username' && (
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
        )}

        {step === 'password' && (
          <div className="form-group">
            <label className="label">Пароль</label>
            <div className="password-wrap">
              <input
                className="input"
                type={showPass ? 'text' : 'password'}
                autoComplete="current-password"
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
        )}

        <button
          className="btn btn-primary"
          type="submit"
          disabled={loading || !username || (step === 'password' && !password)}
          style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
        >
          {loading ? 'Загрузка…' : step === 'username' ? 'Продолжить' : 'Войти'}
        </button>

        {step === 'password' && (
          <button
            type="button"
            onClick={handleBack}
            style={{
              width: '100%',
              marginTop: 8,
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: 13,
              cursor: 'pointer',
              padding: '6px 0',
            }}
          >
            ← Назад
          </button>
        )}
      </form>
    </div>
  )
}
