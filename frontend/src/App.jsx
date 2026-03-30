import { useEffect, useState } from 'react'
import RightBar from './components/layout/RightBar'
import CardsTab from './components/cards/CardsTab'
import TransactionsTab from './components/transactions/TransactionsTab'
import DevicesTab from './components/devices/DevicesTab'
import SettingsPanel from './components/settings/SettingsPanel'
import UsersTab from './components/users/UsersTab'
import LogsTab from './components/logs/LogsTab'
import LoginForm from './components/auth/LoginForm'
import SetupPasswordForm from './components/auth/SetupPasswordForm'
import { checkAuth, logout } from './api/auth'

export default function App() {
  const [user, setUser]                 = useState(undefined) // undefined = загрузка, null = не авторизован
  const [setupUsername, setSetupUsername] = useState(null)
  const [tab, setTab]                   = useState(() => localStorage.getItem('activeTab') ?? 'cards')

  useEffect(() => {
    checkAuth().then(u => setUser(u ?? null))
  }, [])

  const handleTabChange = (t) => {
    localStorage.setItem('activeTab', t)
    setTab(t)
  }

  const handleLogout = async () => {
    await logout()
    setUser(null)
    setSetupUsername(null)
  }

  const handleLoginSuccess = (u) => {
    setUser(u)
    setSetupUsername(null)
  }

  if (user === undefined) {
    return <div className="loader">Загрузка…</div>
  }

  if (setupUsername) {
    return (
      <SetupPasswordForm
        username={setupUsername}
        onSuccess={() => checkAuth().then(u => handleLoginSuccess(u))}
      />
    )
  }

  if (!user) {
    return (
      <LoginForm
        onSuccess={() => checkAuth().then(u => handleLoginSuccess(u))}
        onMustSetPassword={(username) => setSetupUsername(username)}
      />
    )
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <RightBar tab={tab} onTabChange={handleTabChange} onLogout={handleLogout} user={user} />
      <main style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {tab === 'cards'        && <CardsTab currentUser={user} />}
        {tab === 'transactions' && <TransactionsTab />}
        {tab === 'devices'      && <DevicesTab />}
        {tab === 'settings'     && <SettingsPanel />}
        {tab === 'logs'         && <LogsTab />}
        {tab === 'users'        && <UsersTab currentUser={user} />}
      </main>
    </div>
  )
}
