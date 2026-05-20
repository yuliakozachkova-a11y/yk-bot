# Cloud Deploy — YK Media Bot

## Чому
Поточно бот живе на Mac через launchd. При shutdown Mac пости не виходять. Перенос у хмару дає повний 24/7 без залежності від комп'ютера.

## Що зроблено в коді (готово)
- ✅ `Procfile`, `runtime.txt`, `railway.toml`, `render.yaml` створені
- ✅ `.gitignore` оновлений (не пушить .env, БД, медіа, кеші)
- ✅ `.env.example` — шаблон production змінних
- ✅ Git ініціалізовано, файли staged
- ✅ Backup БД: `data/posts.db.backup_2026-05-20_pre-cloud-deploy`

## Що треба від Юлії (10 хвилин)

### Варіант A — Render.com (рекомендую, простіше)

1. **Зайди на https://render.com** → Sign Up через GitHub.
2. **Створи приватний GitHub repo** `yk-bot` через https://github.com/new (Settings → Private).
3. **У моїй наступній сесії** скажи: «починай cloud deploy» → я push код в твій repo.
4. На Render: New → Background Worker → Connect repo `yk-bot` → Render автоматично прочитає `render.yaml`.
5. На Render → Environment → додати **3 секрети**:
   - `TELEGRAM_BOT_TOKEN` = (з мого `.env`)
   - `TELEGRAM_API_ID` = `38946675`
   - `TELEGRAM_API_HASH` = (з мого `.env`)
6. Натиснути **Create Worker** → перший deploy ~3-5 хв.
7. Перевір лог: «Application started».
8. У боті @YK_Media_Bot → /status → має бути ✅ онлайн (бот тепер відповідає з хмари).

### Варіант B — Railway.app (трохи складніше, але дешевше)
Аналогічний flow, але через Railway CLI:
```bash
npm install -g @railway/cli
railway login
railway init
railway up
railway variables set TELEGRAM_BOT_TOKEN=xxx TELEGRAM_API_ID=xxx TELEGRAM_API_HASH=xxx
```

## ⚠️ Critical step: ВИМКНУТИ Mac launchd ПІСЛЯ deploy

Інакше буде 2 боти з одним токеном → конфлікт getUpdates.

```bash
launchctl unload ~/Library/LaunchAgents/com.yk.tgbot.plist
rm ~/Library/LaunchAgents/com.yk.tgbot.plist
```

## Database migration

SQLite файл `data/posts.db` буде створений з нуля в хмарному volume. Щоб перенести існуючі дані (план постів, каталог Drive фото, settings):

1. Загрузити `data/posts.db.backup_2026-05-20_pre-cloud-deploy` у Render через Shell tab:
   ```bash
   # У Render dashboard → Shell
   cp /tmp/upload/posts.db.backup /opt/render/project/src/data/posts.db
   ```
2. Restart worker.

АБО простіше — повторно запустити `scripts/seed_first_week.py` на хмарному воркері — створить базу з нуля з тим же планом.

## Rollback
Якщо щось не так:
```bash
launchctl load ~/Library/LaunchAgents/com.yk.tgbot.plist  # відновити Mac launchd
```
На Render — Suspend worker.
