# CLAUDE.md (güncellenmiş proje kuralları)

## Stack
- Frontend: React + TypeScript (`src/web`)
- Backend: Python 3.12+, FastAPI (`src/api`)
- Database: SQLite

## Klasör Yapısı
- `src/web/` — frontend kodu, component başına dosya
- `src/api/` — backend kodu, route/model/schema ayrımı
- `docs/` — PRD, ARCHITECTURE, feature spec'leri
- `tests/` — src/ ile birebir eşlenen test yapısı

## Kurallar
- Type hints (Python) ve TypeScript tipleri zorunlu
- Her yeni feature için `docs/specs/00N-*.md` yaz