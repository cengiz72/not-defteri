import json
import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

NOTES_FILE = "notes.json"


def load_notes():
    if not os.path.exists(NOTES_FILE):
        return []
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Uyarı: notes.json okunamadı ({e}). Boş liste ile devam ediliyor.")
        return []


def save_notes(notes):
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Hata: notlar kaydedilemedi ({e}).")


def next_id(notes):
    if not notes:
        return 1
    return max(note["id"] for note in notes) + 1


def add_note(notes, text):
    if not text or not text.strip():
        print("Uyarı: boş not eklenemez.")
        return
    note = {
        "id": next_id(notes),
        "text": text.strip(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    notes.append(note)
    save_notes(notes)
    print(f"Not eklendi (id={note['id']}).")


def list_notes(notes):
    if not notes:
        print("Hiç not yok.")
        return
    for note in notes:
        timestamp = note.get("created_at", "-")
        print(f"[{note['id']}] ({timestamp}) {note['text']}")


def delete_note(notes, note_id_str):
    try:
        note_id = int(note_id_str)
    except (TypeError, ValueError):
        print("Uyarı: geçersiz id. Lütfen bir sayı girin.")
        return
    for note in notes:
        if note["id"] == note_id:
            notes.remove(note)
            save_notes(notes)
            print(f"Not silindi (id={note_id}).")
            return
    print(f"Uyarı: id={note_id} bulunamadı.")


def search_notes(notes: list, keyword: str) -> None:
    """Metninde verilen anahtar kelimeyi içeren notları listeler (büyük/küçük harf duyarsız)."""
    if not keyword or not keyword.strip():
        print("Uyarı: arama için bir anahtar kelime girin.")
        return
    keyword = keyword.strip().lower()
    results = [note for note in notes if keyword in note["text"].lower()]
    if not results:
        print(f"'{keyword}' için sonuç bulunamadı.")
        return
    for note in results:
        timestamp = note.get("created_at", "-")
        print(f"[{note['id']}] ({timestamp}) {note['text']}")


def print_help():
    print("Kullanım: python app.py [komut] [argüman]")
    print()
    print("Komutlar:")
    print("  ekle <metin>   - yeni not ekler (zaman damgası otomatik eklenir)")
    print("  listele        - tüm notları listeler")
    print("  sil <id>       - id'ye göre not siler")
    print("  ara <kelime>   - anahtar kelimeyi içeren notları arar")
    print("  yardim, --help, -h - bu mesajı gösterir")
    print("  cikis          - programdan çıkar (yalnızca etkileşimli modda)")
    print()
    print("Komut verilmezse program etkileşimli modda başlar.")


def run_command(notes, command, argument):
    command = command.lower()
    if command == "ekle":
        add_note(notes, argument)
    elif command == "listele":
        list_notes(notes)
    elif command == "sil":
        delete_note(notes, argument)
    elif command == "ara":
        search_notes(notes, argument)
    elif command in ("yardim", "--help", "-h"):
        print_help()
    else:
        print(f"Uyarı: bilinmeyen komut '{command}'. Yardım için 'yardim' veya '--help' yazın.")


def main():
    if len(sys.argv) > 1:
        notes = load_notes()
        command = sys.argv[1]
        argument = " ".join(sys.argv[2:])
        run_command(notes, command, argument)
        return

    notes = load_notes()
    print("Not Defteri'ne hoş geldiniz. Komutlar için 'yardim' veya '--help' yazabilirsiniz.")

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nÇıkılıyor.")
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        if command == "cikis":
            print("Görüşürüz.")
            break

        run_command(notes, command, argument)


if __name__ == "__main__":
    main()