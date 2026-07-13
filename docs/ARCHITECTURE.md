# ARCHITECTURE — Todo App

**Kaynak:** [docs/PRD.md](./PRD.md)
**Durum:** Taslak
**Tarih:** 2026-07-13

> Not: PRD §11 "Deployment" konusunu açık bırakmıştı. Bu doküman deployment hedefini **Render** olarak netleştirir (§7). PRD güncellenene kadar bu doküman deployment kararı için otoriter kaynaktır.

## 1. Stack

| Katman | Teknoloji | Versiyon |
|---|---|---|
| Frontend dili/framework | React + TypeScript | React 18+, TypeScript 5+ |
| Frontend build tool | Vite | 5+ |
| Frontend sunucu state | TanStack React Query | 5+ |
| Frontend form/validasyon | React Hook Form + Zod | — |
| Node runtime | Node.js | 20+ LTS |
| Backend dili/framework | Python + FastAPI | Python 3.12+, FastAPI 0.11x+ |
| Backend ASGI sunucu | Uvicorn | — |
| ORM / migration | SQLAlchemy 2.x + Alembic | — |
| Şema/validasyon | Pydantic | v2 |
| Auth | JWT (python-jose veya pyjwt) + passlib[bcrypt] | — |
| Veritabanı | SQLite (WAL modu) | 3.35+ (WAL/JSON desteği için) |

Stil kütüphanesi seçimi PRD §7'de açık madde olarak bırakılmıştır (CSS Modules ya da Tailwind); bu doküman bir tercih dayatmaz.

## 2. Klasör Sorumlulukları

CLAUDE.md'deki klasör yapısı kuralına (`src/web/`, `src/api/`, `docs/`, `tests/`) dayanır.

### `src/web/`
| Alt klasör | Sorumluluk |
|---|---|
| `src/pages/` | Route seviyesi bileşenler (LoginPage, TaskListPage, vb.) — sayfa kompozisyonu, routing'e bağlı state |
| `src/components/` | Yeniden kullanılabilir, sunum amaçlı bileşenler; component başına bir dosya (CLAUDE.md kuralı) |
| `src/api/` | Backend'e HTTP çağrıları yapan client fonksiyonları + React Query hook'ları (`useTasks`, `useCreateTask` vb.) |
| `src/types/` | Backend Pydantic şemalarıyla birebir eşlenen TS tipleri |
| `src/lib/` | Tarih/timezone dönüşümü, formatlama gibi saf yardımcı fonksiyonlar |
| `src/context/` | Auth/token state (giriş durumu, mevcut kullanıcı) |

### `src/api/`
| Alt klasör | Sorumluluk |
|---|---|
| `routers/` | HTTP endpoint tanımları (`auth.py`, `tasks.py`) — sadece request/response orkestrasyonu, iş mantığı burada olmaz |
| `models/` | SQLAlchemy ORM modelleri (`User`, `Task`) |
| `schemas/` | Pydantic request/response şemaları |
| `services/` | İş mantığı (auth doğrulama, email gönderme soyutlaması, task erişim kontrolü) |
| `db/` | Engine/session kurulumu, WAL pragma ayarı |
| `core/` | Ayarlar (env değişkenleri), güvenlik yardımcıları (JWT encode/decode, password hashing) |
| `alembic/` | Migration script'leri |

`tests/api/` yapısı `src/api/` ile birebir eşlenir (CLAUDE.md kuralı). `tests/web/` klasörü yapı gereği var olur ancak PRD §10 gereği MVP'de otomatik frontend testi yazılmayacağı için şimdilik büyük ölçüde boş kalması beklenir.

## 3. Veri Modeli

PRD §4'ten birebir aktarılmıştır; bu doküman ek bir şema kararı almaz.

### `users`
| Alan | Tip | Kısıt |
|---|---|---|
| id | UUID | PK |
| email | TEXT | UNIQUE, NOT NULL |
| password_hash | TEXT | NOT NULL |
| is_email_verified | BOOLEAN | NOT NULL, default `false` |
| created_at | TIMESTAMP (UTC) | NOT NULL |
| updated_at | TIMESTAMP (UTC) | NOT NULL |

### `tasks`
| Alan | Tip | Kısıt |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → `users.id`, NOT NULL, indexed |
| title | TEXT | NOT NULL, 1–200 karakter |
| description | TEXT | NULL, 0–2000 karakter |
| due_date | TIMESTAMP (UTC) | NULL |
| priority | TEXT (enum: `low`/`medium`/`high`) | NOT NULL, default `medium` |
| is_completed | BOOLEAN | NOT NULL, default `false` |
| deleted_at | TIMESTAMP (UTC) | NULL (soft delete işareti) |
| created_at | TIMESTAMP (UTC) | NOT NULL |
| updated_at | TIMESTAMP (UTC) | NOT NULL |

**Index'ler:** `users.email` (unique), `tasks.user_id`, `tasks(user_id, deleted_at)`, `tasks(user_id, due_date)`.

## 4. API Surface

Base path: `/api`. Auth gerektiren tüm endpoint'ler `Authorization: Bearer <jwt>` header'ı bekler.

### Auth

| Method | Path | Request body | Response |
|---|---|---|---|
| POST | `/auth/register` | `{email, password}` | `201` → `{id, email, is_email_verified}` |
| POST | `/auth/login` | `{email, password}` | `200` → `{access_token, token_type}` |
| POST | `/auth/verify-email` | `{token}` | `200` → `{id, email, is_email_verified: true}` |
| POST | `/auth/forgot-password` | `{email}` | `200` → `{message}` (her zaman aynı mesaj, email enumeration önlenir) |
| POST | `/auth/reset-password` | `{token, new_password}` | `200` → `{message}` |
| GET | `/auth/me` | — | `200` → `{id, email, is_email_verified}` |

### Tasks

| Method | Path | Query/Body | Response |
|---|---|---|---|
| GET | `/tasks` | Query: `status`, `priority`, `due_after`, `due_before`, `sort`, `order`, `page`, `limit` | `200` → `{items: Task[], total, page, limit}` |
| POST | `/tasks` | Body: `{title, description?, due_date?, priority?}` | `201` → `Task` |
| GET | `/tasks/{id}` | — | `200` → `Task` |
| PATCH | `/tasks/{id}` | Body: kısmi `{title?, description?, due_date?, priority?, is_completed?}` | `200` → `Task` |
| DELETE | `/tasks/{id}` | — | `204` (soft delete, body yok) |
| POST | `/tasks/{id}/restore` | — | `200` → `Task` |

`Task` response şekli PRD §4'teki `Task` tablosu alanlarının birebir JSON karşılığıdır (`id, user_id, title, description, due_date, priority, is_completed, created_at, updated_at`; `deleted_at` sadece dahili kullanım, response'ta dönmez).

Yetkilendirme: bir kullanıcı başka bir kullanıcının task'ına eriştiğinde `404` döner (varlığını `403` ile ifşa etmemek için) — bkz. §9 Architectural Decisions.

## 5. Error Handling

Tüm hata yanıtları tek tip zarf kullanır (PRD §5):

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "İnsan tarafından okunabilir mesaj",
    "details": [{"field": "title", "issue": "min_length"}]
  }
}
```

### Status kod convention'ı

| Durum | Status | `error.code` örneği |
|---|---|---|
| Request body/query validasyon hatası (Pydantic) | 422 | `VALIDATION_ERROR` |
| İş kuralı ihlali (örn. süresi dolmuş token) | 400 | `INVALID_TOKEN`, `BAD_REQUEST` |
| Token yok/geçersiz | 401 | `UNAUTHORIZED` |
| Kimliği doğrulanmış ama yetkisi olmayan istek | 403 | `FORBIDDEN` |
| Kayıt bulunamadı veya başka kullanıcıya ait | 404 | `NOT_FOUND` |
| Email zaten kayıtlı | 409 | `EMAIL_ALREADY_EXISTS` |
| Beklenmeyen sunucu hatası | 500 | `INTERNAL_ERROR` |

FastAPI'nin varsayılan `HTTPException` ve `RequestValidationError` handler'ları global exception handler'larla override edilerek yukarıdaki zarfa dönüştürülür; route kodu asla ham FastAPI hata şekli döndürmez.

## 6. Testing Strategy

PRD §10'a dayanır; katman bazında dağılım:

| Katman | Test türü | Araç | Kapsam |
|---|---|---|---|
| `src/api/models/` | Unit | pytest | Alan validasyonu, default değerler, enum kısıtları |
| `src/api/services/` | Unit | pytest | Auth mantığı (hash/verify), email token üretimi/doğrulama, task erişim kontrolü |
| `src/api/routers/` | Integration | pytest + FastAPI `TestClient` + test DB (geçici SQLite dosyası/`:memory:`) | Uçtan uca HTTP akışı: register→verify→login, task CRUD, filtre/sayfalama, yetkilendirme (401/403/404 senaryoları), hata zarfı şekli |
| `src/web/` | — | — | MVP kapsamı dışı (PRD §10); TypeScript strict mode statik kontrol sağlar |

Test dosyaları `tests/api/` altında `src/api/` ile birebir klasör/isim eşlemesiyle yazılır (CLAUDE.md kuralı). Her test dosyası kendi test DB'sini fixture ile izole eder (testler arası state sızıntısı olmaz).

## 7. Deployment Assumptions

Hedef platform: **Render**. İki ayrı servis olarak deploy edilir.

### Backend — Render Web Service
- Runtime: native Python (Docker gerekmez, Render'ın Python buildpack'i yeterli).
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
- Ortam değişkenleri (Render dashboard'unda secret olarak tanımlanır): `JWT_SECRET`, `DATABASE_URL`, `FRONTEND_ORIGIN` (CORS için).

### Frontend — Render Static Site
- Build command: `npm run build`
- Publish directory: `dist`
- Ortam değişkeni: `VITE_API_BASE_URL` (backend servisinin Render URL'i).

### SQLite kalıcılığı — kritik kısıt
Render'ın Web Service'lerinde varsayılan dosya sistemi **ephemeral**'dır: her deploy veya restart'ta sıfırlanır. SQLite dosyası bu diskte tutulursa **her deploy'da tüm veri silinir**. Bu nedenle:
- Backend servisine bir **Render Persistent Disk** eklenir (örn. `/data` mount path'i).
- `DATABASE_URL` bu mount noktasını gösterir (örn. `sqlite:////data/app.db`).
- WAL modu açıkken SQLite üç dosya üretir (`app.db`, `app.db-wal`, `app.db-shm`) — üçü de aynı persistent disk üzerinde olmalıdır.

### Bilinen kısıtlar
- Render Free tier web service'leri inaktivite sonrası "sleep" olur; ilk istekte soğuk başlangıç gecikmesi görülür.
- Persistent disk'e sahip bir servis yatay olarak ölçeklenemez (tek instance) — SQLite zaten tek yazarlı olduğu için bu MVP açısından ek bir kısıt yaratmaz.
- Migration'lar (`alembic upgrade head`) deploy sürecinin bir parçası olarak (build veya release adımında) çalıştırılmalıdır.

## 8. Non-goals

PRD §2'deki kapsam dışı listesiyle birebir aynıdır; mimari bu maddeler için altyapı kurmaz:

- Etiket/kategori, alt görevler (subtasks), tekrarlayan görevler
- Email/push hatırlatmaları (scheduler/background job yok)
- Manuel sürükle-bırak sıralama (`position` alanı yok)
- Gerçek offline destek / PWA (service worker, local cache yok)
- Mobil/responsive tasarım
- Çoklu dil desteği (i18n altyapısı yok)
- Rate limiting / brute-force koruması
- Çoklu cihaz çakışma (conflict) yönetimi — versiyon/ETag kontrolü yok
- Trash (çöp kutusu) görünümü ve retention/cleanup job'ı
- Yatay ölçeklenebilirlik / multi-instance deployment
- Refresh token / token blacklist mekanizması

## 9. Architectural Decisions

| Karar | Neden | Değerlendirilen alternatif |
|---|---|---|
| SQLite (WAL modu) | Tek dosya, sıfır altyapı, MVP/kişisel ölçek için yeterli; PRD'de bilinçli olarak kabul edilen bir trade-off | Postgres (Render managed) — daha iyi concurrency ama MVP için gereksiz operasyonel yük |
| JWT + localStorage | Basit, CSRF altyapısı gerektirmez, frontend/backend ayrık kalır | httpOnly cookie — XSS'e karşı daha güvenli ama SameSite/CSRF token altyapısı gerektirir |
| Refresh token yok | Auth akışını basitleştirir, MVP'de kabul edilebilir sürtünme | Refresh token rotasyonu — daha iyi UX ama token blacklist/revocation karmaşıklığı ekler |
| Soft delete + kısa undo (trash yok) | Kazara silmeye karşı yeterli koruma, UI/DB karmaşıklığı düşük | Tam trash görünümü — daha esnek ama ayrı bir view/endpoint/retention job gerektirir |
| Modal/panel tabanlı task düzenleme | Açıklama+son tarih+öncelik gibi çok alanlı form inline'da kalabalıklaşır | Inline editing — daha az tıklama ama çok alanlı formda UX bozulur |
| Offset/limit sayfalama | Basit, öngörülebilir, `total` sayısı gösterilebilir | Cursor-based — ekleme/silme sırasında offset kaymasını önler ama MVP ölçeğinde gereksiz karmaşıklık |
| Özel hata zarfı (`{error:{code,message}}`) | Frontend'de tek tip hata işleme, tutarlı `code` ile programatik ayırt etme | FastAPI varsayılan hata şekli — daha az iş ama frontend'de tutarsız parsing |
| React Query (TanStack) | Optimistic update, cache invalidation ve loading/error state'leri built-in sağlar | Redux + manuel fetch/cache — aynı davranış için çok daha fazla boilerplate |
| Task erişim ihlalinde `404` (`403` değil) | Başka kullanıcıya ait bir kaydın *varlığını* dahi ifşa etmemek (ID enumeration koruması) | `403 Forbidden` — daha "doğru" HTTP semantiği ama kaydın var olduğunu sızdırır |
| Render + Persistent Disk (Postgres değil) | PRD'de SQLite kararı zaten verildi; Render'da kalıcılık sadece disk mount ile sağlanabilir | Render managed Postgres — kalıcılık sorununu native çözer ama PRD'nin SQLite kararını geçersiz kılar |
