# Правки для публичного доступа через Cloudflare Tunnel

## Что нужно сделать

Одно изменение — полная замена `nginx/nginx.conf`.
Flask (`web-scrcpy/host_server/app.py`) **не трогаем**.

---

## Файл: `nginx/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name _;

        # FastAPI backend
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # React SPA: корень и Vite dev server assets
        location = / {
            proxy_pass http://frontend:3000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        location /@vite/ {
            proxy_pass http://frontend:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
        location /@fs/ {
            proxy_pass http://frontend:3000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }
        location /src/ {
            proxy_pass http://frontend:3000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }
        location /node_modules/ {
            proxy_pass http://frontend:3000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }

        # Flask scrcpy: статика устройств
        location /static/ {
            proxy_pass http://host.docker.internal:5000;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }

        # SocketIO (WebSocket)
        location /socket.io/ {
            proxy_pass http://host.docker.internal:5000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 3600s;
        }

        # Flask scrcpy: страницы устройств /<serial> (catch-all)
        location / {
            proxy_pass http://host.docker.internal:5000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 3600s;
        }
    }
}
```

---

## Логика роутинга

| URL | Куда идёт |
|-----|-----------|
| `domain.com/` | React-панель (frontend:3000) |
| `domain.com/api/v1/...` | FastAPI (backend:8000) |
| `domain.com/SERIALNUMBER` | Flask scrcpy (host:5000) |
| `domain.com/static/...` | Flask scrcpy (host:5000) — его статика |
| `domain.com/socket.io/...` | Flask scrcpy (host:5000) — WebSocket |
| `domain.com/@vite/...` | React Vite dev assets |

React не использует URL-роутинг (нет React Router), поэтому конфликтов нет.

---

## После изменения

```bash
docker compose restart nginx
```

## Проверка

1. `https://domain.com/` → React-панель открывается
2. `https://domain.com/api/v1/cards` → JSON ответ от FastAPI
3. `https://domain.com/SERIALNUMBER` → страница стриминга scrcpy
4. DevTools → Network → WS → SocketIO подключается (статус 101)

---

## Cloudflare Tunnel

Туннель должен указывать на:
- **Service Type**: HTTP
- **URL**: `localhost:80`

Если туннель уже настроен на `:80` — ничего менять не нужно.
