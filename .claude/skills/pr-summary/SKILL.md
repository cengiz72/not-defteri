---
name: pr-summary
description: master branch'e göre değişiklikleri analiz edip PR açıklaması üretir (ne, neden, nasıl test edilir, breaking change).
---

## Değişiklik özeti (stat)

!`git diff main...HEAD --stat`

## Commit geçmişi

!`git log main..HEAD --oneline`

## Talimatlar

1. Yukarıdaki stat özetini ve commit geçmişini kullanarak hangi dosyaların/alanların değiştiğini belirle; gerekirse ilgili dosyaların tam diff'ine (`git diff main...HEAD -- <path>`) bakarak detay çıkar.
2. Aşağıdaki başlıklarla bir PR açıklaması üret:
   - **Ne değişti**: Değişikliklerin kısa, madde madde özeti (dosya/alan bazında)
   - **Neden değişti**: Commit mesajlarından ve kod değişikliğinden çıkarılan motivasyon/gerekçe
   - **Nasıl test edilir**: Reviewer'ın değişikliği doğrulamak için izleyebileceği somut adımlar (ilgiliyse `test-runner` skill'iyle çalıştırılabilecek test path'leri dahil)
   - **Breaking change var mı**: API/schema/davranış değişikliği reviewer'ı veya diğer ekipleri etkiliyorsa açıkça belirt; yoksa "Yok" yaz
3. Emin olmadığın veya diff'ten çıkaramadığın bir gerekçe varsa (özellikle "neden değişti" kısmı) varsayımda bulunmak yerine kullanıcıya sor.
4. Üretilen açıklamayı kullanıcıya göster; PR açma (`gh pr create`) gibi adımlar kullanıcı ayrıca isterse yapılır, bu skill sadece açıklamayı üretir.
