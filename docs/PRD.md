# PRD — Todo App

**Durum:** Taslak — mülakat sonucu onaylandı, implementasyon öncesi son gözden geçirme bekliyor
**Tarih:** 2026-07-13

## 1. Özet

Kullanıcıların hesap oluşturup giriş yaparak kendi görev listelerini yönetebildiği (ekleme, listeleme, filtreleme, tamamlama, silme) bir web uygulaması. Backend FastAPI + SQLite, frontend React + TypeScript.

## 2. Kapsam

### Kapsamda (MVP)
- Email+şifre ile kayıt, giriş, email doğrulama, şifre sıfırlama
- Görev CRUD: başlık, açıklama, son tarih (tarih+saat), öncelik
- Durum/öncelik/tarih aralığı filtreleme, sayfalama
- Soft delete + geri alma (undo)
- Optimistic UI güncellemeleri

### Kapsam dışı (MVP sonrası)
- Etiket/kategori, alt görevler (subtasks), tekrarlayan görevler
- Email/push hatırlatmaları
- Manuel sürükle-bırak sıralama
- Gerçek offline destek / PWA
- Mobil/responsive tasarım
- Çoklu dil desteği (i18n)
- Rate limiting / brute-force koruması
- Çakışma (conflict) yönetimi — tek kullanıcı/tek cihaz varsayılıyor
- Trash (çöp kutusu) görünümü — sadece kısa süreli undo var

## 3. Kullanıcı Modeli & Auth

- Çoklu kullanıcı, her kullanıcının kendi görev listesi var (izolasyon: tüm task sorguları `user_id` ile filtrelenir).
- Kayıt sırasında email doğrulama linki gönderilir (MVP'de **mock**: gerçek SMTP yok, token backend loglarına/console'a yazılır — soyutlama ileride gerçek servise (SendGrid vb.) bağlanabilecek şekilde tek bir `EmailSender` arayüzü arkasında tutulur).
- Şifre sıfırlama (forgot/reset password) akışı aynı mock email mekanizmasıyla çalışır.
- **Tasarım kararı:** Email doğrulanmamış kullanıcı yine de giriş yapabilir; UI'da "email'ini doğrula" uyarı banner'ı gösterilir ama hiçbir işlem engellenmez (MVP'de sürtünmeyi azaltmak için). Bu, gözden geçirilmesi gereken bir karardır.
- Şifreler bcrypt/argon2 ile hash'lenir, düz metin asla saklanmaz.
- Access token: JWT, **localStorage**'da saklanır (basitlik tercih edildi; XSS riski göz önünde bulundurularak render edilen tüm kullanıcı girdisi React'ın otomatik escape'ine bırakılır, `dangerouslySetInnerHTML` kullanılmaz).
- Refresh token akışı yok — token süresi dolunca kullanıcı tekrar giriş yapar.
- Rate limiting / brute-force koruması **MVP kapsamı dışı** (bilinen risk, ileride eklenir).

## 4. Veri Modeli

### User
| Alan | Tip | Not |
|---|---|---|
| id | UUID (PK) | |
| email | str, unique | |
| password_hash | str | |
| is_email_verified | bool | default `false` |
| created_at | datetime (UTC) | |
| updated_at | datetime (UTC) | |

### Task
| Alan | Tip | Not |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID (FK → User) | index |
| title | str, 1–200 karakter | zorunlu, boş olamaz |
| description | str, 0–2000 karakter | opsiyonel |
| due_date | datetime (UTC) | opsiyonel, tarih+saat |
| priority | enum: `low` / `medium` / `high` | default `medium` |
| is_completed | bool | default `false` |
| deleted_at | datetime (UTC), nullable | soft delete işareti |
| created_at | datetime (UTC) | |
| updated_at | datetime (UTC) | |

Index'ler: `user_id`, `(user_id, deleted_at)`, `(user_id, due_date)`.

## 5. API Tasarımı

### Auth
| Method | Path | Açıklama |
|---|---|---|
| POST | `/api/auth/register` | Kayıt, doğrulama email'i (mock) tetiklenir |
| POST | `/api/auth/login` | JWT döner |
| POST | `/api/auth/verify-email` | Token ile email doğrulama |
| POST | `/api/auth/forgot-password` | Reset email'i (mock) tetikler |
| POST | `/api/auth/reset-password` | Token + yeni şifre |
| GET | `/api/auth/me` | Giriş yapmış kullanıcı bilgisi |

### Tasks
| Method | Path | Açıklama |
|---|---|---|
| GET | `/api/tasks` | Filtre + sayfalama: `?status=active\|completed\|all&priority=low,medium,high&due_after=&due_before=&sort=due_date\|priority\|created_at&order=asc\|desc&page=1&limit=20` |
| POST | `/api/tasks` | Yeni görev oluştur |
| GET | `/api/tasks/{id}` | Tek görev |
| PATCH | `/api/tasks/{id}` | Kısmi güncelleme (title, description, due_date, priority, is_completed) |
| DELETE | `/api/tasks/{id}` | Soft delete (`deleted_at` set edilir) |
| POST | `/api/tasks/{id}/restore` | Undo — `deleted_at` temizlenir |

Soft-delete edilmiş görevler hiçbir `GET` sorgusunda dönmez. Kalıcı temizlik (hard delete/retention job) MVP kapsamı dışı.

**Varsayılan sıralama** (kullanıcı sort seçmezse): tamamlanmamış görevler önce, sonra `due_date` artan (null'lar sonda), sonra `priority` azalan (`high`→`low`), sonra `created_at` azalan.

**Sayfalama:** offset/limit tabanlı (`page`, `limit`), response'ta `total` alanı döner. Default `limit=20`.

### Hata Formatı
Tüm hatalar tek tip bir zarfla döner (FastAPI'nin `HTTPException` ve `RequestValidationError` handler'ları override edilir):
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title cannot be empty",
    "details": [{"field": "title", "issue": "min_length"}]
  }
}
```

## 6. Frontend UX

### Sayfalar
- `/register`, `/login`, `/forgot-password`, `/reset-password`, `/verify-email`
- `/` — ana görev listesi (protected route, token yoksa `/login`'e yönlendirir)

### Görev Listesi
- Üstte durum sekmeleri: Tümü / Aktif / Tamamlanan
- Filtre çubuğu: öncelik (çoklu seçim), tarih aralığı
- Sort dropdown: son tarih / öncelik / oluşturma tarihi
- Her satır: tamamlama checkbox'ı, başlık, öncelik rengi (kırmızı=high, sarı=medium, yeşil=low), son tarih (**geçmiş tarihliyse kırmızı vurgulanır**), düzenle/sil aksiyonları
- **Tasarım kararı:** Görev düzenleme bir modal/panel üzerinden yapılır (inline değil) — çünkü açıklama + son tarih + öncelik gibi çok alanlı bir form inline'da kalabalıklaşır. Bu, gözden geçirilmesi gereken bir karardır.
- Silme: soft delete anında gerçekleşir, ekranda 5 saniyelik "Görev silindi [Geri Al]" snackbar'ı gösterilir; geri al'a basılırsa `restore` endpoint'i çağrılır.
- Tüm ekleme/güncelleme/silme işlemleri **optimistic**: UI hemen güncellenir, API çağrısı arka planda yapılır, hata durumunda değişiklik geri alınır ve kullanıcıya bildirim gösterilir.

### Boş / Yükleniyor Durumları
- Görev yokken: illüstrasyon + "İlk görevini ekle" CTA butonu.
- Yükleniyor: skeleton loader'lar (spinner değil).

## 7. Teknik Mimari

- **Frontend:** React + TypeScript, sunucu state yönetimi için React Query (TanStack Query) — optimistic update desteği doğal olarak sağlar. Form validasyonu: React Hook Form + Zod.
- **Stil yaklaşımı:** implementasyon sırasında karar verilecek (CSS Modules ya da Tailwind) — açık madde.
- **Backend:** FastAPI, SQLAlchemy ORM + Alembic migration, Pydantic v2 şemaları.
- **DB:** SQLite, **WAL modu açık** (yazma kilidi çakışmasını azaltmak için). Çoklu kullanıcı ortamında SQLite'ın dosya seviyesi yazma kilidi bilinen bir kısıt olarak kabul edildi; MVP/kişisel ölçek için yeterli görüldü. Postgres'e geçiş formal bir gereksinim değil ama SQLAlchemy kullanımı geçişi zaten kolaylaştırır.
- **Timezone:** Tüm `datetime` alanları UTC olarak saklanır; frontend kullanıcının local timezone'ına çevirip gösterir.
- **CORS:** Sadece frontend origin'ine izin verilir.

## 8. Edge Case'ler

- Boş/whitespace-only başlık → 422 validasyon hatası.
- Başlık > 200 karakter, açıklama > 2000 karakter → 422.
- Son tarih geçmişte bir görev oluşturma engellenmez (kullanıcı geçmiş bir işi loglamak isteyebilir), sadece listede "gecikmiş" olarak vurgulanır.
- Aynı görev iki sekme/cihazdan aynı anda düzenlenirse: **ele alınmıyor** (tek kullanıcı/tek cihaz varsayımı, son yazan kazanır — özel bir çakışma kontrolü yok).
- Silinmiş (soft-deleted) bir görev `restore` sonrası tüm filtrelerde normal göreve döner.
- Kayıtlı olmayan/yanlış email ile login → generic "geçersiz email veya şifre" mesajı (email enumeration'ı önlemek için, hangisinin yanlış olduğu belirtilmez).
- Doğrulama/reset token'ları tek kullanımlık ve süreli (örn. 1 saat) olur; süresi dolmuş token → 400 hatası.

## 9. Güvenlik

- Şifreler bcrypt/argon2 ile hash'lenir.
- JWT localStorage'da saklanır (XSS riski bilinen bir trade-off; CSRF riski yok çünkü cookie kullanılmıyor).
- Kullanıcı girdisi (title/description) render edilirken React'ın otomatik escape'ine güvenilir; backend'de de uzunluk/whitespace validasyonu yapılır.
- Rate limiting / brute-force koruma **kapsam dışı** — bilinen risk olarak not düşülür.

## 10. Test Stratejisi

- Backend: pytest ile unit + API (route) testleri — model validasyonu, auth akışları (kayıt/login/doğrulama/reset), task CRUD, filtre/sayfalama, yetkilendirme (kullanıcı başka kullanıcının görevine erişemez), edge case'ler (boş başlık, karakter limiti, geçersiz token).
- Test yapısı `tests/api/` altında `src/api/` ile birebir eşlenir (CLAUDE.md kuralı).
- Frontend'de otomatik test **kapsam dışı** (MVP'de sadece backend testi hedefleniyor); TypeScript strict mode tip güvenliği sağlar.

## 11. Deployment

Henüz karara bağlanmadı — MVP local geliştirmeye odaklanıyor. İleride docker-compose ile local/production ayağa kaldırma değerlendirilecek.

## 12. Açık Kararlar / Gözden Geçirme Gereken Noktalar

Aşağıdakiler mülakatta doğrudan sorulmadı, PRD yazılırken makul varsayımlarla karara bağlandı — implementasyona başlamadan önce onaylanmalı:

1. Email doğrulanmamış kullanıcının girişe izin verilmesi (§3).
2. Görev düzenlemenin modal/panel üzerinden yapılması, inline değil (§6).
3. Frontend stil kütüphanesi seçimi (§7).
4. Login hata mesajının generic tutulması (email enumeration koruması) (§8).
