---
paths:
  - tests/**
  - test_*.py
---

# Test Kuralları

- Framework: pytest kullan (unittest değil)
- Her test fonksiyonuna açıklayıcı docstring yaz
- Test isimleri `test_<ne_test_ediliyor>_<beklenen_sonuç>` formatında
- Fixture'ları `conftest.py`'de topla
- Coverage hedefi: %80+
- Mock kullanırken `unittest.mock.patch` tercih et