import { useCallback, useEffect, useState } from 'react'
import { listCards } from '../../api/cards'
import { useDebounce } from '../../hooks/useDebounce'
import CardModal from './CardModal'
import CardSidebar from './CardSidebar'

const LIMIT = 50

export default function CardsTab() {
  const [cards, setCards]       = useState([])
  const [total, setTotal]       = useState(0)
  const [page, setPage]         = useState(1)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  const [search, setSearch]     = useState('')
  const [bankFilter, setBankFilter] = useState('')
  const [groupFilter, setGroupFilter] = useState('')

  const [showModal, setShowModal]   = useState(false)
  const [selectedCard, setSelectedCard] = useState(null)

  const debouncedSearch = useDebounce(search, 300)

  const load = useCallback(async (p = page) => {
    setLoading(true)
    setError(null)
    try {
      const data = await listCards({
        search: debouncedSearch || undefined,
        bank: bankFilter || undefined,
        group: groupFilter || undefined,
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
  useEffect(() => { load(page) }, [page, debouncedSearch, bankFilter, groupFilter])  // eslint-disable-line

  const totalPages = Math.max(1, Math.ceil(total / LIMIT))

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—'

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
          className="btn btn-primary"
          style={{ marginLeft: 'auto' }}
          onClick={() => setShowModal(true)}
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
                    <th>Дата покупки</th>
                    <th>Группа</th>
                  </tr>
                </thead>
                <tbody>
                  {cards.length === 0 ? (
                    <tr>
                      <td colSpan={6}>
                        <div className="empty-state">
                          <div>Нет карт</div>
                          <p>Добавьте карту через кнопку выше или Telegram-бота</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    cards.map(card => (
                      <tr key={card.id} onClick={() => setSelectedCard(card)}>
                        <td>{card.full_name}</td>
                        <td>{card.bank || '—'}</td>
                        <td className="td-mono">{card.card_number}</td>
                        <td>{card.phone_number || '—'}</td>
                        <td>{fmtDate(card.purchase_date)}</td>
                        <td>{card.group_name || '—'}</td>
                      </tr>
                    ))
                  )}
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
                >
                  ←
                </button>
                <button
                  className="btn btn-ghost btn-sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                >
                  →
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {showModal && (
        <CardModal
          onClose={() => setShowModal(false)}
          onCreated={() => load(1)}
        />
      )}

      <CardSidebar
        card={selectedCard}
        onClose={() => setSelectedCard(null)}
        onUpdated={(updated) => {
          setSelectedCard(updated)
          load(page)
        }}
      />
    </div>
  )
}
