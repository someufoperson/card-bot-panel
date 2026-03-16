import { api } from './client'

export const listDevices    = ()         => api.get('/devices')
export const releaseSession = (deviceId) => api.delete(`/devices/${deviceId}/session`)
