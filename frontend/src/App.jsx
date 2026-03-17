import { useState } from 'react'
import RightBar from './components/layout/RightBar'
import CardsTab from './components/cards/CardsTab'
import TransactionsTab from './components/transactions/TransactionsTab'
import DevicesTab from './components/devices/DevicesTab'
import SettingsPanel from './components/settings/SettingsPanel'

export default function App() {
  const [tab, setTab] = useState(() => localStorage.getItem('activeTab') ?? 'cards')

  const handleTabChange = (t) => {
    localStorage.setItem('activeTab', t)
    setTab(t)
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <RightBar tab={tab} onTabChange={handleTabChange} />
      <main style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {tab === 'cards'        && <CardsTab />}
        {tab === 'transactions' && <TransactionsTab />}
        {tab === 'devices'      && <DevicesTab />}
        {tab === 'settings'     && <SettingsPanel />}
      </main>
    </div>
  )
}
