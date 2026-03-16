import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { listSettings } from '../api/settings'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [settings, setSettings] = useState({})

  const loadSettings = useCallback(async () => {
    try {
      const list = await listSettings()
      const map = {}
      list.forEach(s => { map[s.key] = s.value })
      setSettings(map)
    } catch {
      // settings unavailable — use defaults
    }
  }, [])

  useEffect(() => { loadSettings() }, [loadSettings])

  return (
    <AppContext.Provider value={{ settings, reloadSettings: loadSettings }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
