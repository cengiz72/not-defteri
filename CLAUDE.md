# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack
- Python 3.12+
- FastAPI
- SQLite (veritabanı)

## Build & Test
- Kurulum: `pip install -r requirements.txt`
- Çalıştır: `uvicorn main:app`
- Test: `pytest --cov`

## Naming Convention
- Değişken ve fonksiyon isimleri: snake_case

## Error Handling
- Bare `except:` kullanma; her zaman spesifik exception yakala
- Dosya I/O işlemlerinde context manager (`with`) kullan

## Diğer Kurallar
- Her fonksiyona type hints ekle
- Her public fonksiyona docstring yaz
- Commit mesajları Conventional Commits formatında
