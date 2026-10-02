"""
core/tahta.py — Tahtanın kimliği: hangi derslikte olduğu ve mikrofon durumu.

Her akıllı tahta belirli bir sınıfta durur (10-A, 11-B, 12-C…). Bu bilgi
arayüzde görünür ve sistem promptuna girer — Aybüke hangi sınıfa ders
verdiğini bilir, sınıf düzeyini öğretmene ayrıca sormaz.

`config/api_keys.json` içindeki `derslik` alanından okunur, elle yazılır.
"""

import json
import re
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

# "10-A", "10A", "10 A", "12-c" -> ("10", "A")
_DERSLIK_RE = re.compile(r"^\s*(\d{1,2})\s*[-/ ]?\s*([A-Za-zÇĞİÖŞÜçğıöşü]?)\s*$")


def derslik() -> str:
    """Tahtanın bulunduğu derslik, örn. '10-A'. Tanımsızsa boş dize."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            ham = str(json.load(f).get("derslik", "")).strip()
    except Exception:
        return ""
    if not ham:
        return ""
    m = _DERSLIK_RE.match(ham)
    if not m:
        return ham          # beklenmedik biçim: olduğu gibi göster
    sinif, sube = m.group(1), m.group(2).upper()
    return f"{sinif}-{sube}" if sube else sinif


def sinif_duzeyi() -> str:
    """
    Derslikten sınıf düzeyini çıkar: '10-A' -> '10'.

    Sistem promptuna sınıf düzeyi olarak girer.
    """
    d = derslik()
    m = re.match(r"^(\d{1,2})", d)
    return m.group(1) if m else ""


_MIKROFON_YOK = {"false", "yok", "kapali", "kapalı", "hayir", "hayır", "0", "no", "off"}


def mikrofon_var() -> bool:
    """
    Bu tahtada kullanılabilir bir mikrofon var mı? Config'teki `mikrofon`
    alanı `false` ise Aybüke MİKROFONSUZ MODDA çalışır — ses girişi hiç
    açılmaz, ders tek yönlü anlatılır.

    Alan yoksa ya da dosya okunamıyorsa True: eski tahtalarda davranış
    değişmesin. Mikrofon tamir edilen tahtada alan silinir ya da `true` yapılır.
    """
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            deger = json.load(f).get("mikrofon", True)
    except Exception:
        return True
    if isinstance(deger, bool):
        return deger
    return str(deger).strip().lower() not in _MIKROFON_YOK


def etiket() -> str:
    """Arayüzde gösterilecek etiket. Tanımsızsa uyarı metni döner."""
    d = derslik()
    return d if d else "DERSLİK TANIMSIZ"
