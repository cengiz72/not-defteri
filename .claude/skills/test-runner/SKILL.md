---
name: test-runner
description: Testleri çalıştırır (opsiyonel olarak belirli bir path için), başarısız olanları analiz edip kaynak koddaki hatayı düzeltir.
allowed-tools: ["Bash"]
---

## Talimatlar

1. `$ARGUMENTS` verilmişse, sadece o path'teki test(ler)i çalıştır:
   - Path `tests/` altında ve `src/api` ile eşleşiyorsa (Python/FastAPI backend) → `pytest $ARGUMENTS`
   - Path `.ts`/`.tsx`/`src/web` ile ilgiliyse (React/TypeScript frontend) → önce `package.json` içindeki test script'ini kontrol et (`npm test -- $ARGUMENTS` veya `vitest run $ARGUMENTS` gibi), ona göre çalıştır
   - Path'in hangi tarafa ait olduğu belirsizse önce dosyanın nerede olduğuna bak, gerekirse her iki runner'ı da dene
2. `$ARGUMENTS` verilmemişse tüm test suite'ini çalıştır:
   - Backend: `pytest`
   - Frontend: `npm test` (veya repo'da tanımlı eşdeğer script)
3. Çıktıyı analiz et, başarısız testleri listele.
4. Her başarısız test için:
   - Hata/traceback'i oku, kök nedeni belirle
   - Testin kendisi değil, ilgili kaynak koddaki (`src/api` veya `src/web`) hatayı düzelt — test zaten yanlış/eski yazılmışsa bunu düzeltmeden önce kullanıcıya belirt
   - Düzeltmeden sonra sadece o testi tekrar çalıştırarak doğrula
5. Tüm düzeltmeler bittikten sonra ilgili test grubunu (ya da tüm suite'i) yeniden çalıştırıp regresyon olmadığını doğrula.
6. Kullanıcıya kısa bir özet ver: kaç test geçti/kaldı, hangi dosyalarda ne düzeltildi.
