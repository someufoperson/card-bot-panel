import { useState } from 'react'
import Header from './components/layout/Header'
import CardsTab from './components/cards/CardsTab'
import TransactionsTab from './components/transactions/TransactionsTab'
import DevicesTab from './components/devices/DevicesTab'
import SettingsPanel from './components/settings/SettingsPanel'

export default function App() {
  const [tab, setTab] = useState('cards')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Header tab={tab} onTabChange={setTab} />
      <main style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {tab === 'cards'        && <CardsTab />}
        {tab === 'transactions' && <TransactionsTab />}
        {tab === 'devices'      && <DevicesTab />}
        {tab === 'settings'     && <SettingsPanel />}
      </main>
    </div>
  )
}
