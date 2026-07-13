# Plan — İlk CRUD Endpoint: POST /api/tasks

## Context

Repo şu anda tamamen greenfield: `src/api/`, `src/web/`, `tests/api/`, `tests/web/` boş klasörler; `requirements.txt`, `alembic.ini`, `.env`, DB dosyası, `package.json` hiçbiri yok. Kullanıcı, Todo App'in ilk CRUD endpoint'i olan `POST /api/tasks` için (spec içinde `POST /api/todos` olarak anıldı, ama `docs/specs/001-gorev-olustur.md` ile PRD/ARCHITECTURE'a göre doğru path `/api/tasks`) adım adım bir uygulama planı istiyor — kod yazılmayacak, sadece plan.

Bu plan üç kaynağa harfiyen sadık kalır: `docs/PRD.md` (veri modeli, güvenlik), `docs/ARCHITECTURE.md` (klasör sorumlulukları, API surface, hata formatı, test stratejisi, deployment), `docs/specs/001-gorev-olustur.md` (endpoint sözleşmesi, validasyon kuralları, 11 adet test case adı). Kullanıcıyla netleştirilen kapsam kararları:
- **Auth kapsamı:** Sadece JWT altyapısı (`core/security.py` + `get_current_user`) kurulur; `/auth/register`/`/auth/login` HTTP endpoint'leri bu planın dışında — testler token'ı doğrudan `create_access_token()` ile üretir.
- **Migration:** Alembic baştan kurulur; ilk migration `users` + `tasks` tablolarını oluşturur.
- **Test DB kurulumu:** Tam sadakat — testler her seferinde gerçek `alembic upgrade head` çalıştırır (create_all() bypass edilmez), migration dosyasının kendisi de test edilmiş olur.

Bu planın onaylanmasının ardından tek çıktı, bu içeriğin `docs/plans/gun04-ilk-crud-plani.md` dosyasına yazılmasıdır — başka hiçbir kod dosyası oluşturulmayacak.

## Adım Adım Plan

### 1. `requirements.txt` (repo kökü)
Render build command'ı (`pip install -r requirements.txt`, ARCHITECTURE §7) bunu repo kökünde bekler. Paketler:
- `fastapi`, `uvicorn[standard]`
- `sqlalchemy>=2.0`, `alembic`
- `pydantic>=2`, `pydantic-settings`
- `PyJWT` (ARCHITECTURE §1'de `python-jose` ile birlikte iki seçenekten biri olarak sunulmuştu; PyJWT daha küçük API yüzeyi ve daha aktif bakım nedeniyle seçildi), `passlib[bcrypt]` (ARCHITECTURE §1'de zaten net), `bcrypt<4.0.0` (passlib'in bcrypt 4.x ile bilinen uyumsuzluğunu önlemek için gerekli pin)
- `pytest`, `httpx` (FastAPI `TestClient`'ın httpx tabanlı olması nedeniyle açık bağımlılık)

### 2. `src/api/core/` — ayarlar ve güvenlik
- **`config.py`**: `pydantic-settings` ile `Settings(BaseSettings)` — `database_url` (default `sqlite:///./app.db`), `jwt_secret`, `jwt_algorithm` (default `HS256`), `jwt_expire_minutes` (default `60` — PRD'de sayı verilmemiş, makul varsayım), `frontend_origin` (CORS için). Modül seviyesinde `settings = Settings()` singleton.
- **`security.py`**:
  - `hash_password` / `verify_password` — `passlib.context.CryptContext(schemes=["bcrypt"])` sarmalayıcıları; sadece test kullanıcısını seed etmek için kullanılır ama gerçek/yeniden kullanılabilir kod (ileride login endpoint'i bunu tekrar kullanacak).
  - `create_access_token(user_id: UUID, expires_delta=None) -> str` — `sub` claim'i kullanıcı UUID'si, `exp` claim'i `jwt_expire_minutes`'tan hesaplanır.
  - `decode_access_token(token: str) -> UUID` — imza/expiry doğrular, `sub`'ı döner; geçersizse PyJWT'nin exception'ı yukarı taşınır.
  - `get_current_user(token, db) -> User` — `fastapi.security.HTTPBearer` ile header'ı okur (OAuth2PasswordBearer değil, çünkü login formu akışı yok), `decode_access_token` çağırır, DB'den kullanıcıyı yükler; header yok/token geçersiz/kullanıcı yoksa `UnauthorizedError` fırlatır (§8'de 401'e map edilir).

### 3. `src/api/db/session.py` — engine/session
- `engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})`
- `connect` event listener: her yeni bağlantıda `PRAGMA journal_mode=WAL;` ve `PRAGMA foreign_keys=ON;` çalıştırır (ARCHITECTURE §2'nin `db/` sorumluluğu).
- `SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)`
- `get_db()` — FastAPI dependency, session yield edip `finally`'de kapatır.
- `Base` bilerek burada değil `models/base.py`'de tanımlanır (db↔models arasında dairesel import'u önlemek için).

### 4. `src/api/models/` — SQLAlchemy modelleri
- **`base.py`**: `class Base(DeclarativeBase): pass`
- **`user.py`** — PRD §4 ile birebir: `id` (UUID PK), `email` (unique, indexed), `password_hash`, `is_email_verified` (default False), `created_at`/`updated_at`. `tasks` relationship.
- **`task.py`** — PRD §4 ile birebir: `id` (UUID PK), `user_id` (FK→users.id, indexed), `title` (String(200) — 1-200/boş-olamaz kuralı DB seviyesinde değil Pydantic'te uygulanır), `description` (String(2000), nullable), `due_date` (DateTime(timezone=True), nullable), `priority` (paylaşılan `Priority(str, Enum)` — low/medium/high/highest — hem model hem şema bunu import eder, default `medium`), `is_completed` (Boolean, default False), `deleted_at` (nullable), `created_at`/`updated_at`. `__table_args__` ile composite index'ler: `(user_id, deleted_at)` ve `(user_id, due_date)` — `user_id` tekil index'i kolon üzerindeki `index=True` ile zaten oluşur. PRD §4'teki üç index'le birebir eşleşir.
- **`__init__.py`**: `Base`, `User`, `Task`, `Priority`'yi re-export eder — Alembic'in `Base.metadata`'yı tam görebilmesi için gerekli.

### 5. Alembic kurulumu
- `alembic.ini` **repo kökünde** (diğer tüm kök-invoke edilen komutlarla tutarlı), `script_location = src/api/alembic`.
- `src/api/alembic/env.py`: `from src.api.models import Base`, `target_metadata = Base.metadata`; `settings.database_url`'i `config.set_main_option("sqlalchemy.url", ...)` ile runtime'da enjekte eder (Render'ın persistent-disk `DATABASE_URL`'iyle tutarlı).
- İlk migration (`alembic revision --autogenerate -m "create users and tasks tables"`): `users` + `tasks` tablolarını (FK sırasına göre `users` önce) ve üç index'i oluşturur. Autogenerate sonrası elle doğrulanacaklar: `users.email` unique index, `tasks`'taki üç index, `priority` alanının SQLite'ta `CHECK` constraint'e derlenmiş `sa.Enum` olarak göründüğü.

### 6. `src/api/schemas/task.py` — Pydantic şemaları
- **`TaskCreate`**: `title: str = Field(min_length=1, max_length=200)` + `@field_validator("title")` ile `.strip()` sonrası boşsa hata (whitespace-only reddi); değer **trim edilmeden** olduğu gibi saklanır (spec trim'i şart koşmuyor). `description: str | None = Field(default=None, max_length=2000)`. `due_date: datetime | None = None` — Pydantic v2 ISO 8601'i native parse eder, geçersiz format otomatik 422 üretir; offset'li datetime'lar UTC'ye normalize edilir. `priority: Priority | None = None` (default atama burada değil, service katmanında — business rule ayrımı ARCHITECTURE'ın "iş mantığı services'te" kuralına uyar).
- **`TaskRead`**: `id, user_id, title, description, due_date, priority, is_completed, created_at, updated_at` (`deleted_at` asla yok). `model_config = ConfigDict(from_attributes=True)`.

### 7. `src/api/services/task_service.py`
`create_task(db, user_id, data: TaskCreate) -> Task`: `priority = data.priority or Priority.medium` (default kuralı burada uygulanır), `Task(user_id=..., is_completed=False, ...)` oluşturur (`is_completed` request'ten asla gelmez), `db.add/commit/refresh`, döner.

### 8. `src/api/core/errors.py` — global hata zarfı
- `AppError` taban sınıfı (`code`, `message`, `status_code`, `details`) + `UnauthorizedError` (401/`UNAUTHORIZED`) — diğer alt sınıflar (`NotFoundError` vb.) ARCHITECTURE §5 tablosuna göre ileride eklenecek şekilde stub bırakılabilir.
- `RequestValidationError` handler → `422` + `{error:{code:"VALIDATION_ERROR", message, details:[{field, issue}, ...]}}`.
- `AppError` handler → `exc.status_code` + `{error:{code, message, details}}`.
- `StarletteHTTPException` fallback handler → raw FastAPI şekli asla dışarı sızmaz.
- Genel `Exception` handler → `500`/`INTERNAL_ERROR`.
Tüm handler'lar `main.py`'de `app`'e register edilir — ARCHITECTURE §5'in "route kodu asla ham FastAPI hata şekli döndürmez" kuralı.

### 9. `src/api/routers/tasks.py`
`router = APIRouter(prefix="/tasks", tags=["tasks"])`; `POST ""` — `data: TaskCreate` gövdesini alır, `get_current_user` + `get_db` dependency'lerini kullanır, `task_service.create_task` çağırır, `TaskRead.model_validate(task)` döner, `status_code=201`. Router'da iş mantığı yok — sadece orkestrasyon.

### 10. `src/api/main.py`
`FastAPI()` app; `frontend_origin`'e kısıtlı CORS middleware (PRD §9/ARCHITECTURE §7); §8'deki 4 handler register; `tasks.router` `prefix="/api"` ile include edilir (final path: `/api/tasks`). `on_startup`'ta `create_all()` **yok** — tablo oluşturma tamamen Alembic'in sorumluluğunda kalır.

### 11. Test altyapısı — `tests/api/conftest.py`
- **Test DB stratejisi:** `tmp_path` ile temp dosya tabanlı SQLite (`:memory:` değil — SQLAlchemy connection pooling'in in-memory SQLite'ta her bağlantıyı ayrı/boş bir DB'ye açması bilinen bir tuzak; dosya tabanlı yaklaşım production'daki WAL/dosya davranışını daha sadık simüle eder).
- **Migration sadakati (kullanıcı kararı):** `db_engine(tmp_path)` fixture'ı, geçici DB dosyasına karşı gerçek `alembic upgrade head`'i programatik olarak çalıştırır (`alembic.config.Config` ile `sqlalchemy.url`'i temp path'e set edip `alembic.command.upgrade(cfg, "head")` çağırarak) — `Base.metadata.create_all()` **kullanılmaz**, migration dosyasının kendisi her test koşumunda doğrulanmış olur. Bunun getirdiği yavaşlık kabul edilmiş bir trade-off.
- `db_session(db_engine)` — session açar, test sonunda kapatır/rollback.
- `client(db_engine)` — `app.dependency_overrides[get_db]`'yi temp DB'ye bağlı session'a override eder, `TestClient(app)` döner.
- `test_user(db_session)` — gerçek `hash_password` ile bir `User` satırı ekler, döner.
- `auth_headers(test_user)` — `create_access_token(test_user.id)`'i doğrudan çağırır (HTTP login yok), `{"Authorization": "Bearer <token>"}` döner.
- Tüm fixture'lar function-scoped — testler arası state sızıntısı olmaz (ARCHITECTURE §6).

### 12. `tests/api/routers/test_tasks.py` — 11 test case
| Test | Ne doğrular |
|---|---|
| `test_create_task_success_minimal` | Sadece `title` + geçerli auth → `201`; `is_completed:false`, `priority:"medium"`, `description`/`due_date` null |
| `test_create_task_success_full_fields` | Tüm alanlarla POST → `201`; response tüm gönderilen alanları birebir yansıtır |
| `test_create_task_default_priority_is_medium` | `priority` verilmeden POST → `priority == "medium"` |
| `test_create_task_empty_title_fails` | `title:""` → `422 VALIDATION_ERROR` |
| `test_create_task_whitespace_title_fails` | `title:"   "` → `422 VALIDATION_ERROR` |
| `test_create_task_title_too_long_fails` | 201 karakterlik `title` → `422` |
| `test_create_task_description_too_long_fails` | 2001 karakterlik `description` → `422` |
| `test_create_task_invalid_priority_fails` | `priority:"urgent"` → `422` |
| `test_create_task_invalid_due_date_format_fails` | `due_date:"not-a-date"` → `422` |
| `test_create_task_without_auth_fails` | `Authorization` header yok → `401 UNAUTHORIZED`; DB'ye hiçbir `Task` satırı yazılmadığı da doğrulanır |
| `test_create_task_persists_with_correct_user_id` | POST sonrası DB'den `id` ile sorgulanan `Task.user_id == test_user.id` |

### 13. Manuel Uçtan Uca Doğrulama
1. `pip install -r requirements.txt`
2. `.env`'de `JWT_SECRET` set edilir (`DATABASE_URL` default'ta kalabilir)
3. `alembic upgrade head` — `app.db` (+ WAL dosyaları) oluşur
4. Tek seferlik bir Python snippet'i ile bir `User` seed edilir ve `create_access_token` ile token üretilir (login endpoint'i olmadığı için manuel test için tek yol)
5. `uvicorn src.api.main:app --reload`
6. `curl -X POST http://localhost:8000/api/tasks -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"title":"Buy milk"}'` → `201` + tam `TaskRead` JSON
7. Aynı istek `Authorization` header'sız → `401` + hata zarfı
8. `-d '{"title":""}'` → `422` + `details` dolu hata zarfı
9. `sqlite3 app.db "select id,user_id,title,priority,is_completed from tasks;"` ile satırın gerçekten yazıldığı doğrulanır
10. `pytest tests/api/routers/test_tasks.py -v` — 11 test de geçer; `app.db`'nin (adım 3'ten kalan) test koşumundan etkilenmediği kontrol edilir (izolasyon kanıtı)

## Bu Planda Alınan Küçük Varsayımlar (dokümanlarda net belirtilmemiş)
- JWT kütüphanesi: PyJWT (python-jose yerine)
- `bcrypt<4.0.0` pin — passlib uyumluluğu için zorunlu
- `pydantic-settings` env yönetimi için
- `jwt_expire_minutes` default 60
- `title` trim edilmeden saklanır, sadece whitespace-only kontrolü için strip edilir
- `due_date` offset'li ISO 8601 kabul edilip UTC'ye normalize edilir
- `alembic.ini` repo kökünde
- `Priority` default'unun schema değil service katmanında uygulanması

## Nihai Çıktı
Onay sonrası tek işlem: yukarıdaki içerik `docs/plans/gun04-ilk-crud-plani.md` dosyasına yazılmasıdır — başka hiçbir kod dosyası oluşturulmayacak.
