const BASE = '/api/v1/users'

export async function listUsers() {
  const res = await fetch(BASE)
  if (!res.ok) throw new Error('Ошибка загрузки пользователей')
  return res.json()
}

export async function listUsernames() {
  const res = await fetch(BASE + '/usernames')
  if (!res.ok) return []
  return res.json()
}

export async function createUser(username, role) {
  const res = await fetch(BASE + '/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, role }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Ошибка' }))
    throw new Error(err.detail || 'Ошибка')
  }
  return res.json()
}

export async function deleteUser(id) {
  const res = await fetch(`${BASE}/${id}`, { method: 'DELETE' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Ошибка' }))
    throw new Error(err.detail || 'Ошибка')
  }
}

export async function resetUserPassword(id) {
  const res = await fetch(`${BASE}/${id}/reset-password`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Ошибка' }))
    throw new Error(err.detail || 'Ошибка')
  }
  return res.json()
}
