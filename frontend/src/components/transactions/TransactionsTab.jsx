export default function TransactionsTab() {
  return (
    <div>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Карта</th>
              <th>Сумма</th>
              <th>Валюта</th>
              <th>Тип</th>
              <th>Получатель / Отправитель</th>
              <th>Источник</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={7}>
                <div className="empty-state">
                  <div>Транзакций нет</div>
                  <p>Заполнится автоматически в Phase 2 через Telegram-бота</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
