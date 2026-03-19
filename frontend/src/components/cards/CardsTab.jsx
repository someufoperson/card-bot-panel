import { useCallback, useEffect, useState } from 'react'
import { deleteCard, listCards, sendCards } from '../../api/cards'
import { useApp } from '../../context/AppContext'
import { useDebounce } from '../../hooks/useDebounce'
import { useSSE } from '../../hooks/useSSE'
import CardModal from './CardModal'
import CardEditModal from './CardEditModal'

const LIMIT = 50

const fmtMoney = (v) => v != null ? Number(v).toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'

export default function CardsTab() {
  const { settings } = useApp()
  const [copiedId, setCopiedId] = useState(null)
  const [cards, setCards]     = useState([])
  const [total, setTotal]     = useState(0)
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const [search, setSearch] = useState('')

  const [selected, setSelected] = useState(new Set())

  const [sortCol, setSortCol] = useState(null)   // null | 'balance' | 'turnover'
  const [sortDir, setSortDir] = useState('asc')  // 'asc' | 'desc'

  const [sending, setSending] = useState(false)
  const [toast, setToast]     = useState(null) // { message, type: 'success'|'error' }

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const [showAddModal, setShowAddModal] = useState(false)
  const [editCard, setEditCard]         = useState(null)

  const debouncedSearch = useDebounce(search, 300)

  const load = useCallback(async (p = page) => {
    setLoading(true)
    setError(null)
    try {
      const data = await listCards({
        search: debouncedSearch || undefined,
        page: p,
        limit: LIMIT,
      })
      setCards(data.items)
      setTotal(data.total)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [debouncedSearch, page])

  useEffect(() => { setPage(1) }, [debouncedSearch])
  useEffect(() => { load(page) }, [page, debouncedSearch]) // eslint-disable-line

  useSSE((e) => { if (e.type === 'cards_updated') load(page) })

  const totalPages = Math.max(1, Math.ceil(total / LIMIT))
  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—'

  const toggleSort = (col) => {
    if (sortCol !== col) { setSortCol(col); setSortDir('asc') }
    else if (sortDir === 'asc') setSortDir('desc')
    else { setSortCol(null); setSortDir('asc') }
  }

  const sortedCards = [...cards].sort((a, b) => {
    const aBlocked = !!a.active_block
    const bBlocked = !!b.active_block
    if (aBlocked !== bBlocked) return aBlocked - bBlocked

    const nameCmp = (a.full_name || '').localeCompare(b.full_name || '', 'ru')

    if (sortCol === 'balance') {
      const cmp = (a.balance ?? 0) - (b.balance ?? 0)
      return cmp !== 0 ? (sortDir === 'asc' ? cmp : -cmp) : nameCmp
    }
    if (sortCol === 'turnover') {
      const cmp = (a.monthly_turnover ?? 0) - (b.monthly_turnover ?? 0)
      return cmp !== 0 ? (sortDir === 'asc' ? cmp : -cmp) : nameCmp
    }

    return nameCmp
  })

  const handleSend = async () => {
    if (selected.size === 0 || sending) return
    setSending(true)
    try {
      await sendCards([...selected])
      showToast('Карты отправлены')
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setSending(false)
    }
  }

  const handleDelete = async (card, e) => {
    e.stopPropagation()
    if (!window.confirm(`Удалить карту ${card.full_name}?`)) return
    try {
      await deleteCard(card.id)
      load(page)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="toolbar">
        <input
          className="input"
          placeholder="Поиск по картам"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <button
          className="btn btn-secondary"
          style={{ marginLeft: 'auto' }}
          disabled={selected.size === 0 || sending}
          onClick={handleSend}
        >
          {sending ? 'Отправка…' : 'Отправить карты'}
        </button>
        <button
          className="btn btn-primary"
          onClick={() => setShowAddModal(true)}
        >
          + Добавить карту
        </button>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {error && (
          <div style={{ padding: 16, color: 'var(--danger)', fontSize: 13 }}>{error}</div>
        )}
        {loading && <div className="loader">Загрузка…</div>}
        {!loading && !error && (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th style={{ width: 36 }}>
                      <input
                        type="checkbox"
                        checked={sortedCards.length > 0 && sortedCards.every(c => selected.has(c.id))}
                        onChange={e => setSelected(e.target.checked ? new Set(sortedCards.map(c => c.id)) : new Set())}
                      />
                    </th>
                    <th>ФИО</th>
                    <th>Банк</th>
                    <th>Номер карты</th>
                    <th>Телефон</th>
                    <th style={{ cursor: 'pointer', userSelect: 'none' }} onClick={() => toggleSort('balance')}>
                      Баланс {sortCol === 'balance' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
                    </th>
                    <th style={{ cursor: 'pointer', userSelect: 'none' }} onClick={() => toggleSort('turnover')}>
                      Оборот за месяц {sortCol === 'turnover' ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
                    </th>
                    <th>Пользователь</th>
                    <th>Блокировка</th>
                    <th style={{ width: 80 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {cards.length === 0 ? (
                    <tr>
                      <td colSpan={10}>
                        <div className="empty-state">
                          <div>Нет карт</div>
                          <p>Добавьте карту через кнопку выше или Telegram-бота</p>
                        </div>
                      </td>
                    </tr>
                  ) : sortedCards.map(card => {
                    const blocked = !!card.active_block
                    return (
                      <tr
                        key={card.id}
                        onClick={() => setEditCard(card)}
                        style={{ cursor: 'pointer' }}
                      >
                        <td onClick={e => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={selected.has(card.id)}
                            onChange={e => setSelected(prev => {
                              const next = new Set(prev)
                              e.target.checked ? next.add(card.id) : next.delete(card.id)
                              return next
                            })}
                          />
                        </td>
                        <td>{card.full_name}</td>
                        <td>{card.bank || '—'}</td>
                        <td className="td-mono">{card.card_number}</td>
                        <td>{card.phone_number || '—'}</td>
                        <td>{fmtMoney(card.balance)}</td>
                        <td>{fmtMoney(card.monthly_turnover)}</td>
                        <td>{card.responsible_user || '—'}</td>
                        <td>
                          <span style={{
                            padding: '2px 8px', borderRadius: 4, fontSize: 11,
                            background: blocked ? 'var(--danger)' : 'var(--bg-hover)',
                            color: blocked ? '#fff' : 'var(--text-muted)',
                          }}>
                            {blocked ? 'Заблок.' : 'Отсутствует'}
                          </span>
                        </td>
                        <td onClick={e => e.stopPropagation()}>
                          <button
                            className="btn btn-ghost btn-sm"
                            disabled={!card.device}
                            onClick={() => {
                              if (!card.device) return
                              const domain = settings.device_domain || 'http://localhost'
                              navigator.clipboard.writeText(`${domain}/${card.device.serial}`)
                              setCopiedId(card.id)
                              setTimeout(() => setCopiedId(null), 2000)
                            }}
                          >
                            Копировать ссылку
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {total > LIMIT && (
              <div className="pagination" style={{ padding: '12px 16px' }}>
                <span>{total} карт · стр. {page} / {totalPages}</span>
                <button
                  className="btn btn-ghost btn-sm"
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                >←</button>
                <button
                  className="btn btn-ghost btn-sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                >→</button>
              </div>
            )}
          </>
        )}
      </div>

      {showAddModal && (
        <CardModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => load(1)}
        />
      )}

      {editCard && (
        <CardEditModal
          card={editCard}
          onClose={() => setEditCard(null)}
          onUpdated={(updated) => {
            setCards(cs => cs.map(c => c.id === updated.id ? updated : c))
            setEditCard(updated)
          }}
          onDeleted={() => {
            setCards(cs => cs.filter(c => c.id !== editCard.id))
            setEditCard(null)
          }}
        />
      )}

      {copiedId && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 999,
          background: 'var(--success)', color: '#fff',
          padding: '10px 18px', borderRadius: 8, fontSize: 13,
          boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
        }}>
          Ссылка скопирована
        </div>
      )}

      {toast && (
        <div style={{
          position: 'fixed', bottom: copiedId ? 68 : 24, right: 24, zIndex: 999,
          background: toast.type === 'error' ? 'var(--danger)' : 'var(--success)',
          color: '#fff',
          padding: '10px 18px', borderRadius: 8, fontSize: 13,
          boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
        }}>
          {toast.message}
        </div>
      )}
    </div>
  )
}
