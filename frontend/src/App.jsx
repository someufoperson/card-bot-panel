import { useEffect, useState } from 'react'
import RightBar from './components/layout/RightBar'
import CardsTab from './components/cards/CardsTab'
import TransactionsTab from './components/transactions/TransactionsTab'
import DevicesTab from './components/devices/DevicesTab'
import SettingsPanel from './components/settings/SettingsPanel'
import LoginForm from './components/auth/LoginForm'
import { checkAuth, logout } from './api/auth'

export default function App() {
  const [authed, setAuthed] = useState(null) // null = загрузка
  const [tab, setTab] = useState(() => localStorage.getItem('activeTab') ?? 'cards')

  useEffect(() => {
    checkAuth().then(user => setAuthed(!!user))
  }, [])

  const handleTabChange = (t) => {
    localStorage.setItem('activeTab', t)
    setTab(t)
  }

  const handleLogout = async () => {
    await logout()
    setAuthed(false)
  }

  if (authed === null) {
    return <div className="loader">Загрузка…</div>
  }

  if (!authed) {
    return <LoginForm onSuccess={() => setAuthed(true)} />
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <RightBar tab={tab} onTabChange={handleTabChange} onLogout={handleLogout} />
      <main style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {tab === 'cards'        && <CardsTab />}
        {tab === 'transactions' && <TransactionsTab />}
        {tab === 'devices'      && <DevicesTab />}
        {tab === 'settings'     && <SettingsPanel />}
      </main>
    </div>
  )
}
