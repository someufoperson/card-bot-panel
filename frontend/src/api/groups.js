import { api } from './client'

export const listGroups   = (type)     => api.get('/groups', { params: type ? { type } : {} })
export const createGroup  = (name, type) => api.post('/groups', { name, type })
export const deleteGroup  = (id)       => api.delete(`/groups/${id}`)
