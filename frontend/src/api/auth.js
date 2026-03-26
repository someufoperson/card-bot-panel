const BASE = '/api/v1/auth'

export async function checkAuth() {
  const res = await fetch(`${BASE}/me`)
  if (res.ok) return await res.json()
  return null
}

export async function login(username, password) {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Ошибка входа' }))
    throw new Error(err.detail || 'Ошибка входа')
  }
  return res.json()
}

export async function logout() {
  await fetch(`${BASE}/logout`, { method: 'POST' })
}
