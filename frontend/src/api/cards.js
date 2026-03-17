import { api } from './client'

export function listCards({ search, bank, group, page = 1, limit = 50 } = {}) {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  if (bank)   params.set('bank', bank)
  if (group)  params.set('group', group)
  params.set('page', page)
  params.set('limit', limit)
  return api.get(`/cards?${params}`)
}

export const listCardNames  = ()         => api.get('/cards/names')
export const createCard     = (data)     => api.post('/cards', data)
export const getCard        = (id)       => api.get(`/cards/${id}`)
export const updateCard     = (id, data) => api.put(`/cards/${id}`, data)
export const deleteCard     = (id)       => api.delete(`/cards/${id}`)
export const getCardTxns    = (id)       => api.get(`/cards/${id}/transactions`)
export const blockCard      = (id, blockedAt)   => api.post(`/cards/${id}/blocks`, blockedAt ? { blocked_at: blockedAt } : {})
export const unblockCard    = (id, unblockedAt) => api.delete(`/cards/${id}/blocks/active`, unblockedAt ? { unblocked_at: unblockedAt } : undefined)
export const getCardBlocks  = (id)       => api.get(`/cards/${id}/blocks`)
