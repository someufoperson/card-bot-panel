# Ваши данные
$token = "8797640909:AAEUZfqfXjw-_ROvAigidqBd_RkAH4SZhjI"
$chatId = -1003730321063

# Получаем данные о последнем входе (Event ID 4624 — успешный вход)
# $event = Get-WinEvent -LogName "Security" -MaxEvents 1 | Where-Object {$_.Id -eq 4624}

# Извлекаем имя пользователя и IP-адрес
# $userName = $event.Properties[5].Value
# $remoteIP = $event.Properties[18].Value
$computerName = $env:COMPUTERNAME
$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Текст сообщения
$message = "🔔 *Вход на сервер RDS*`n`n" +
        #    "👤 *Пользователь:* $userName`n" +
        #    "🌐 *IP-адрес:* $remoteIP`n" +
           "🖥 *Сервер:* $computerName`n" +
           "⏰ *Время:* $date"

# Отправка в Telegram
$url = "https://api.telegram.org/bot$token/sendMessage"
$body = @{
    chat_id = $chatId
    text = $message
    parse_mode = "Markdown"
}

Invoke-RestMethod -Uri $url -Method Post -Body $body