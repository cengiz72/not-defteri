# CLI Not Defteri — Proje Kuralları

## Stack
- Python 3.12+
- SQLite (veritabanı)
- click (CLI framework) — henüz eklenmemişse argparse kullan

## Build & Test
- Kurulum: `pip install -r requirements.txt`
- Çalıştır: `python main.py`
- Test: `pytest tests/`

## Kurallar
- Her fonksiyona type hints ekle
- Her public fonksiyona docstring yaz
- Error handling zorunlu: bare `except:` kullanma, spesifik exception yakala
- Dosya I/O işlemlerinde context manager (`with`) kullan
- Değişken/fonksiyon isimleri snake_case
- Commit mesajları Conventional Commits formatında