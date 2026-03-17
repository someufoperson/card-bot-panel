import { useCallback, useEffect, useState } from 'react'
import { deleteCard, listCards } from '../../api/cards'
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

  const [search, setSearch]           = useState('')
  const [bankFilter, setBankFilter]   = useState('')
  const [groupFilter, setGroupFilter] = useState('')

  const [blockSort, setBlockSort] = useState(0) // 0=нет, 1=незаблок. выше, 2=заблок. выше

  const [showAddModal, setShowAddModal]   = useState(false)
  const [editCard, setEditCard]           = useState(null)

  const debouncedSearch = useDebounce(search, 300)

  const load = useCallback(async (p = page) => {
    setLoading(true)
    setError(null)
    try {
      const data = await listCards({
        search: debouncedSearch || undefined,
        bank:   bankFilter     || undefined,
        group:  groupFilter    || undefined,
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
  }, [debouncedSearch, bankFilter, groupFilter, page])

  useEffect(() => { setPage(1) }, [debouncedSearch, bankFilter, groupFilter])
  useEffect(() => { load(page) }, [page, debouncedSearch, bankFilter, groupFilter]) // eslint-disable-line

  useSSE((e) => { if (e.type === 'cards_updated') load(page) })

  const totalPages = Math.max(1, Math.ceil(total / LIMIT))
  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—'

  const SORT_LABELS = ['Блокировка ↕', 'Незаблок. ↑', 'Заблок. ↑']
  const sortedCards = blockSort === 0 ? cards : [...cards].sort((a, b) => {
    const aBlocked = !!a.active_block
    const bBlocked = !!b.active_block
    if (blockSort === 1) return aBlocked - bBlocked   // незаблок. выше
    if (blockSort === 2) return bBlocked - aBlocked   // заблок. выше  // eslint-disable-line
    return 0
  })

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
          placeholder="Поиск по ФИО, банку, последним 4 цифрам…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <input
          className="input"
          style={{ maxWidth: 160 }}
          placeholder="Банк"
          value={bankFilter}
          onChange={e => setBankFilter(e.target.value)}
        />
        <input
          className="input"
          style={{ maxWidth: 160 }}
          placeholder="Группа"
          value={groupFilter}
          onChange={e => setGroupFilter(e.target.value)}
        />
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => setBlockSort(s => (s + 1) % 3)}
        >
          {SORT_LABELS[blockSort]}
        </button>
        <button
          className="btn btn-primary"
          style={{ marginLeft: 'auto' }}
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
                    <th>ФИО</th>
                    <th>Банк</th>
                    <th>Номер карты</th>
                    <th>Телефон</th>
                    <th>Баланс</th>
                    <th>Оборот за месяц</th>
                    <th>Пользователь</th>
                    <th>Дата покупки</th>
                    <th>Блокировка</th>
                    <th>Дата блокировки</th>
                    <th>Дата забора</th>
                    <th>Группа</th>
                    <th>Комментарий</th>
                    <th style={{ width: 80 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {cards.length === 0 ? (
                    <tr>
                      <td colSpan={14}>
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
                        <td>{card.full_name}</td>
                        <td>{card.bank || '—'}</td>
                        <td className="td-mono">{card.card_number}</td>
                        <td>{card.phone_number || '—'}</td>
                        <td>{fmtMoney(card.balance)}</td>
                        <td>{fmtMoney(card.monthly_turnover)}</td>
                        <td>{card.responsible_user || '—'}</td>
                        <td>{fmtDate(card.purchase_date)}</td>
                        <td>
                          <span style={{
                            padding: '2px 8px', borderRadius: 4, fontSize: 11,
                            background: blocked ? 'var(--danger)' : 'var(--bg-hover)',
                            color: blocked ? '#fff' : 'var(--text-muted)',
                          }}>
                            {blocked ? 'Заблок.' : 'Отсутствует'}
                          </span>
                        </td>
                        <td>{blocked ? fmtDate(card.active_block.blocked_at) : '—'}</td>
                        <td>{card.pickup_date ? fmtDate(card.pickup_date) : '—'}</td>
                        <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {card.group_name || '—'}
                        </td>
                        <td style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {card.comment || '—'}
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
    </div>
  )
}
