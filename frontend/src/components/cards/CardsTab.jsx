import { useCallback, useEffect, useState } from 'react'
import { deleteCard, listCards, updateCard } from '../../api/cards'
import { useDebounce } from '../../hooks/useDebounce'
import CardModal from './CardModal'
import CardSidebar from './CardSidebar'

const LIMIT = 50

const EMPTY_FORM = (card) => ({
  full_name:    card.full_name    ?? '',
  bank:         card.bank         ?? '',
  card_number:  card.card_number  ?? '',
  phone_number: card.phone_number ?? '',
  group_name:   card.group_name   ?? '',
})

export default function CardsTab() {
  const [cards, setCards]     = useState([])
  const [total, setTotal]     = useState(0)
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const [search, setSearch]         = useState('')
  const [bankFilter, setBankFilter] = useState('')
  const [groupFilter, setGroupFilter] = useState('')

  const [showModal, setShowModal]       = useState(false)
  const [selectedCard, setSelectedCard] = useState(null)

  // Inline row editing
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm]   = useState({})
  const [saving, setSaving]       = useState(false)
  const [rowError, setRowError]   = useState(null)

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

  const totalPages = Math.max(1, Math.ceil(total / LIMIT))
  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—'

  const startEdit = (card, e) => {
    e.stopPropagation()
    setEditingId(card.id)
    setEditForm(EMPTY_FORM(card))
    setRowError(null)
  }

  const cancelEdit = (e) => {
    e?.stopPropagation()
    setEditingId(null)
    setRowError(null)
  }

  const handleSave = async (card, e) => {
    e.stopPropagation()
    setSaving(true)
    setRowError(null)
    try {
      const payload = {}
      Object.entries(editForm).forEach(([k, v]) => { payload[k] = v.trim() || null })
      const updated = await updateCard(card.id, payload)
      setCards(cs => cs.map(c => c.id === card.id ? updated : c))
      if (selectedCard?.id === card.id) setSelectedCard(updated)
      setEditingId(null)
    } catch (err) {
      setRowError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (card, e) => {
    e.stopPropagation()
    if (!window.confirm(`Удалить карту ${card.full_name}?`)) return
    try {
      await deleteCard(card.id)
      if (selectedCard?.id === card.id) setSelectedCard(null)
      load(page)
    } catch (err) {
      setError(err.message)
    }
  }

  const setField = (key, value) => setEditForm(f => ({ ...f, [key]: value }))

  // Inline input cell
  const EditCell = ({ field, mono }) => (
    <td onClick={e => e.stopPropagation()}>
      <input
        className={`input${mono ? ' mono' : ''}`}
        style={{ padding: '4px 8px', fontSize: 12 }}
        value={editForm[field]}
        onChange={e => setField(field, e.target.value)}
      />
    </td>
  )

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

      {rowError && (
        <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 8 }}>{rowError}</div>
      )}

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
                    <th style={{ width: 140 }}></th>
                  </tr>
                </thead>
                <tbody>
                  {cards.length === 0 ? (
                    <tr>
                      <td colSpan={7}>
                        <div className="empty-state">
                          <div>Нет карт</div>
                          <p>Добавьте карту через кнопку выше или Telegram-бота</p>
                        </div>
                      </td>
                    </tr>
                  ) : cards.map(card => {
                    const isEditing = editingId === card.id
                    return (
                      <tr
                        key={card.id}
                        onClick={() => !isEditing && setSelectedCard(card)}
                        style={{ cursor: isEditing ? 'default' : 'pointer' }}
                      >
                        {isEditing ? (
                          <>
                            <EditCell field="full_name" />
                            <EditCell field="bank" />
                            <EditCell field="card_number" mono />
                            <EditCell field="phone_number" />
                            <td>{fmtDate(card.purchase_date)}</td>
                            <EditCell field="group_name" />
                          </>
                        ) : (
                          <>
                            <td>{card.full_name}</td>
                            <td>{card.bank || '—'}</td>
                            <td className="td-mono">{card.card_number}</td>
                            <td>{card.phone_number || '—'}</td>
                            <td>{fmtDate(card.purchase_date)}</td>
                            <td>{card.group_name || '—'}</td>
                          </>
                        )}

                        <td onClick={e => e.stopPropagation()}>
                          <div style={{ display: 'flex', gap: 4 }}>
                            {isEditing ? (
                              <>
                                <button
                                  className="btn btn-primary btn-sm"
                                  disabled={saving}
                                  onClick={e => handleSave(card, e)}
                                >
                                  {saving ? '…' : 'Сохранить'}
                                </button>
                                <button
                                  className="btn btn-ghost btn-sm"
                                  disabled={saving}
                                  onClick={cancelEdit}
                                >
                                  Отмена
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  className="btn btn-ghost btn-sm"
                                  onClick={e => startEdit(card, e)}
                                >
                                  Изменить
                                </button>
                                <button
                                  className="btn btn-danger btn-sm"
                                  onClick={e => handleDelete(card, e)}
                                >
                                  Удалить
                                </button>
                              </>
                            )}
                          </div>
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
