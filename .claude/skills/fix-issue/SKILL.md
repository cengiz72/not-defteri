---
name: fix-issue
description: Bir GitHub issue numarasını okuyup plan yapar, implement eder, test eder ve özet sunar.
---

## Issue içeriği

!`gh issue view $ARGUMENTS`

## Workflow

1. **Oku**: Yukarıdaki issue başlığını, açıklamasını ve varsa yorumlarını analiz et. Ne istendiğini ve kabul kriterlerini netleştir. Belirsiz bir nokta varsa varsayımda bulunmadan önce kullanıcıya sor.
2. **Plan yap**: CLAUDE.md'deki klasör yapısına göre (`src/api`, `src/web`, `docs/`, `tests/`) hangi dosyaların değişeceğini belirle. Değişiklik trivial değilse (yeni feature, birden fazla dosya, mimari etki) plan modunu kullanarak kullanıcıdan onay al; küçük/bariz düzeltmelerde direkt implementasyona geç.
3. **Implement et**: Onaylanan plana göre kodu yaz. Type hints (Python) ve TypeScript tiplerini eksiksiz tut. Yeni bir feature ekleniyorsa `docs/specs/00N-*.md` dosyasını da oluştur.
4. **Test et**: Değişikliğin kapsadığı testleri çalıştır ve başarısız olanları düzelt — bunun için `test-runner` skill'ini kullan (gerekirse `$ARGUMENTS` yerine ilgili test path'ini vererek).
5. **Özet ver**: Issue numarasına referansla ne değiştiğini, hangi dosyaların etkilendiğini ve test sonucunu kısaca özetle. Commit atma veya PR açma gibi adımlar kullanıcı ayrıca isterse yapılır, bu skill kapsamında değildir.
