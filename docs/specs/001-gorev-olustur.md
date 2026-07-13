# Feature 001 — Görev Oluştur

**Kaynak:** [docs/PRD.md](../PRD.md) §4–5, [docs/ARCHITECTURE.md](../ARCHITECTURE.md) §3–5

## User Story
Giriş yapmış bir kullanıcı olarak, en azından bir başlık girerek yeni bir görev oluşturabilmek istiyorum ki yapılacaklarımı takip edebileyim.

## API Contract

```
POST /api/tasks
Authorization: Bearer <jwt>   (zorunlu)
```

**Request:**
```json
{
  "title": "string",
  "description": "string | null",
  "due_date": "string (ISO 8601, UTC) | null",
  "priority": "low | medium | high | null"
}
```
`title` dışındaki tüm alanlar opsiyoneldir. `priority` verilmezse `medium` varsayılır.

**Response — `201 Created`:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "string",
  "description": "string | null",
  "due_date": "string (ISO 8601, UTC) | null",
  "priority": "low | medium | high",
  "is_completed": false,
  "created_at": "string (ISO 8601, UTC)",
  "updated_at": "string (ISO 8601, UTC)"
}
```
`is_completed` request'te kabul edilmez — yeni görev her zaman `false` ile başlar. `id` sunucu tarafından üretilen bir UUID'dir; `user_id` token'dan çözülür, request body'sinde gelmez.

**Hata yanıtları** ([ARCHITECTURE.md §5](../ARCHITECTURE.md#5-error-handling) zarfı ile):
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }
```

## Validation Rules
- `title`: zorunlu, boş veya sadece boşluktan oluşamaz, 1–200 karakter
- `description`: opsiyonel, 0–2000 karakter
- `due_date`: opsiyonel, geçerli ISO 8601 UTC datetime olmalı; geçmiş bir tarih **engellenmez** (PRD §8 — kullanıcı geçmişe dönük bir işi loglayabilir)
- `priority`: opsiyonel, yalnızca `low` / `medium` / `high`; başka bir değer geçersiz
- `Authorization` header zorunlu ve geçerli bir JWT içermeli

## Error Cases
| Senaryo | Status | `error.code` |
|---|---|---|
| `title` boş/whitespace-only | 422 | `VALIDATION_ERROR` |
| `title` > 200 karakter | 422 | `VALIDATION_ERROR` |
| `description` > 2000 karakter | 422 | `VALIDATION_ERROR` |
| `priority` geçersiz değer | 422 | `VALIDATION_ERROR` |
| `due_date` geçersiz format | 422 | `VALIDATION_ERROR` |
| `Authorization` header yok/geçersiz token | 401 | `UNAUTHORIZED` |

## Acceptance Criteria
- [ ] Sadece `title` ile POST → `201`, `priority` varsayılan olarak `medium`, `is_completed: false`
- [ ] `title` + `description` + `due_date` + `priority` ile POST → `201`, tüm alanlar response'ta doğru dönüyor
- [ ] Boş/whitespace `title` ile POST → `422 VALIDATION_ERROR`
- [ ] `title` 201 karakter ile POST → `422 VALIDATION_ERROR`
- [ ] `description` 2001 karakter ile POST → `422 VALIDATION_ERROR`
- [ ] Geçersiz `priority` (örn. `"urgent"`) ile POST → `422 VALIDATION_ERROR`
- [ ] `Authorization` header olmadan POST → `401 UNAUTHORIZED`
- [ ] Oluşturulan görev veritabanında, token'daki kullanıcıya ait `user_id` ile görünüyor
- [ ] `created_at` ve `updated_at` UTC olarak set ediliyor

## Test Cases
`tests/api/routers/test_tasks.py`
- `test_create_task_success_minimal` — sadece `title`
- `test_create_task_success_full_fields`
- `test_create_task_default_priority_is_medium`
- `test_create_task_empty_title_fails`
- `test_create_task_whitespace_title_fails`
- `test_create_task_title_too_long_fails`
- `test_create_task_description_too_long_fails`
- `test_create_task_invalid_priority_fails`
- `test_create_task_invalid_due_date_format_fails`
- `test_create_task_without_auth_fails`
- `test_create_task_persists_with_correct_user_id`

## Kapsam Dışı (bu feature için)
- Görev listeleme/filtreleme → Feature 002
- Güncelleme/tamamlama → ayrı feature
- Silme/undo → ayrı feature
