import { api } from './client'

export const listDevices    = ()               => api.get('/devices')
export const createDevice   = (data)           => api.post('/devices', data)
export const updateDevice   = (serial, data)   => api.patch(`/devices/${serial}`, data)
export const deleteDevice   = (serial)         => api.delete(`/devices/${serial}`)
export const releaseSession = (serial)         => api.delete(`/devices/${serial}/session`)
export const setAccess      = (serial, status) => api.patch(`/devices/${serial}/access/${status}`)
export const setAccessAll   = (status)         => api.patch(`/devices/access/all/${status}`)
export const getAllDeviceLogs = ()              => api.get('/devices/logs')
export const getDeviceLogs   = (serial)        => api.get(`/devices/${serial}/logs`)
