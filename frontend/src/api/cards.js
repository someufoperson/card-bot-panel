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

export const createCard   = (data)       => api.post('/cards', data)
export const getCard      = (id)         => api.get(`/cards/${id}`)
export const updateCard   = (id, data)   => api.put(`/cards/${id}`, data)
export const deleteCard   = (id)         => api.delete(`/cards/${id}`)
export const getCardTxns  = (id)         => api.get(`/cards/${id}/transactions`)
