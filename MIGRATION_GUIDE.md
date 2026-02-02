# Применение миграции для добавления полей клиента

## Описание
Миграция добавляет в таблицу `users` поля для хранения данных клиента из внешнего API:
- `external_id` - внешний ID клиента
- `name` - имя клиента
- `email` - email
- `balance` - баланс
- `birthday` - дата рождения
- `sex` - пол (0=женский, 1=мужской, null=неизвестно)
- `available_tickets` - количество доступных билетов
- `additional_fields` - дополнительные поля (JSON)
- `updated_at` - дата последнего обновления

## Применение миграции

### В Docker
```bash
# Остановить контейнеры
docker-compose down

# Пересобрать и запустить (миграция применится автоматически)
docker-compose up -d --build

# Проверить логи
docker-compose logs -f bot
```

### Локально (если используете)
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Применить миграцию
python -m alembic upgrade head
```

## Синхронизация существующих пользователей

После применения миграции нужно синхронизировать данные существующих пользователей:

```bash
# В Docker
docker-compose exec bot python scripts/sync_users_from_api.py

# Локально
python scripts/sync_users_from_api.py
```

## Автоматическая синхронизация

Данные клиента автоматически загружаются из API:
- При регистрации нового пользователя (после share phone)
- Можно добавить периодическую синхронизацию при каждом запросе билета

## Проверка

После применения миграции проверьте структуру таблицы:

```bash
# В Docker
docker-compose exec db psql -U lottery_user -d lottery_bot -c "\d users"

# Локально
psql -U lottery_user -d lottery_bot -c "\d users"
```

Должны появиться новые колонки.

## Откат (если нужно)

```bash
# В Docker
docker-compose exec bot python -m alembic downgrade -1

# Локально
python -m alembic downgrade -1
```
