const BASE = '/api/v1/auth'

export async function checkAuth() {
  const res = await fetch(`${BASE}/me`)
  if (res.ok) return await res.json() // { username, role }
  return null
}

export async function login(username, password) {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password: password || null }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Ошибка входа' }))
    throw new Error(err.detail || 'Ошибка входа')
  }
  return res.json() // { ok, must_set_password? }
}

export async function setupPassword(username, newPassword) {
  const res = await fetch(`${BASE}/setup-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, new_password: newPassword }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Ошибка' }))
    throw new Error(err.detail || 'Ошибка')
  }
  return res.json()
}

export async function logout() {
  await fetch(`${BASE}/logout`, { method: 'POST' })
}
