# Tools

اسکریپت‌های migration و seed با Poetry Poe.

## Migration کامل از dump

```bash
# پیش‌نمایش بدون commit
poetry run poe migrate-all --dry-run

# import/upsert همه داده‌ها از kio-bot.sql
poetry run poe migrate-all

# با overwrite
poetry run poe migrate-all --overwrite
```

مراحل به ترتیب: users → sponsors → games → scores → lang_codes (ru→tr) → sequences

## Migration تکی

```bash
poetry run poe migrate-users
poetry run poe migrate-games
poetry run poe migrate-scores
poetry run poe migrate-sponsors
poetry run poe migrate-lang-codes
poetry run poe migrate-sequences
```

## اسپانسرها

```bash
poetry run poe add-sponsors --json '[{"id":-100123,"name":"Channel","link":"https://t.me/example"}]'
poetry run poe add-sponsors --file sponsors.json
```

## اجرا روی سرور (Docker)

```bash
# poe در image production نیست؛ از poetry script استفاده کنید:
docker compose run --rm --no-deps --entrypoint="" bot poetry run migrate-all
```

## Dump

فایل `kio-bot.sql` شامل schema + COPY data برای:
- `app_user` (~120 کاربر)
- `app_game` (~513 بازی)
- `app_score` (~147 امتیاز)
- `app_sponser` (خالی در dump فعلی)

Migration idempotent است: ردیف‌های موجود skip می‌شوند مگر `--overwrite`.
