---
name: commit
description: Staged değişiklikleri analiz edip conventional commit mesajı öneren, onay sonrası commit atan skill.
disable-model-invocation: true
---

## Staged diff

!`git diff --cached`

## Talimatlar

1. Yukarıdaki staged diff'i analiz et.
2. Diff boşsa (staged değişiklik yoksa) kullanıcıya bunu bildir ve dur, commit atma.
3. Değişikliklere uygun bir Conventional Commits mesajı öner: `type(scope): description`
   - `type` seçenekleri: feat, fix, docs, refactor, test, chore, style, perf, build, ci
   - `scope`, etkilenen alanı yansıtsın (ör. api, web, docs)
   - `description` kısa, emir kipinde ve İngilizce ya da projenin mevcut commit diliyle tutarlı olsun
4. `$ARGUMENTS` verilmişse, önerilen commit mesajının gövdesine ek bir not satırı olarak ekle.
5. Önerilen commit mesajını kullanıcıya göster ve onay iste. Kullanıcı onaylamadan commit ATMA.
6. Kullanıcı onaylarsa (mesajı aynen ya da düzenleyerek kabul ederse) `git commit -m "..."` ile commit'i oluştur.
7. Sadece zaten staged olan değişiklikleri commitle; ek dosya stage etme.
