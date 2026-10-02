"""
core/saglayicilar.py — Zamansız metin ve görü görevleri, doğrudan Gemini ile.

Canlı ses oturumunun dışındaki işler (arama sonucu sentezi, YouTube özeti,
yüklenen dosya ya da ekran görüntüsü okuma) buradan geçer. Ayrı bir sunucu,
yerel model ya da başka bir sağlayıcı yoktur: canlı oturumla AYNI Gemini
anahtar havuzu (`core/anahtar.py`) ve `core/modeller.py::METIN_MODELI`
kullanılır. Bu çağrılar canlı oturumla aynı kotayı paylaşır.

Sözleşme: `metin_uret` / `gorsel_uret` düz `str` döner; başarısızlıkta
`RuntimeError` YÜKSELİR, asla boş ya da uydurma bir yanıt dönmez. Çağıran
taraf bunu kendi "uydurma, sınırlı devam et" metnine çevirir.

Bu fonksiyonlar iş parçacıklarında çağrılır — bu yüzden senkron istemci.
"""

from core import anahtar as core_anahtar
from core.modeller import METIN_MODELI

ZAMAN_ASIMI_MS = 60_000


def _istemci(api_anahtari: str):
    from google import genai
    return genai.Client(api_key=api_anahtari,
                        http_options={"timeout": ZAMAN_ASIMI_MS})


def _uret(icerik, sistem: str | None, gorev: str) -> str:
    """Bir kez dener; kota hatasında havuzdaki sıradaki anahtarla bir kez daha."""
    from google.genai import types

    yapilandirma = types.GenerateContentConfig(
        system_instruction=sistem or None,
        temperature=0.3,
    )
    son_hata: Exception | None = None
    for deneme in range(2):
        try:
            # İstemci bir değişkende TUTULMALI: `_istemci(...).models...`
            # zincirinde geçici nesne istek bitmeden çöp toplanıp kendi HTTP
            # bağlantısını kapatıyor ("client has been closed").
            istemci = _istemci(core_anahtar.simdiki())
            yanit = istemci.models.generate_content(
                model=METIN_MODELI, contents=icerik, config=yapilandirma,
            )
            metin = (getattr(yanit, "text", None) or "").strip()
            if not metin:
                raise RuntimeError(f"'{gorev}' görevi boş yanıt döndü.")
            return metin
        except Exception as e:
            son_hata = e
            if deneme == 0 and core_anahtar.kota_hatasi_mi(e) \
                    and core_anahtar.sonrakine_gec():
                continue
            break
    raise RuntimeError(f"'{gorev}' görevi başarısız: "
                       f"{type(son_hata).__name__}: {son_hata}")


def metin_uret(gorev: str, istem: str, sistem: str | None = None) -> str:
    """Salt metin görevler (özet, sentez, analiz, düzeltme)."""
    return _uret(istem, sistem, gorev)


def gorsel_uret(gorev: str, istem: str, resim_bytes: bytes, mime: str = "image/jpeg",
                sistem: str | None = None) -> str:
    """İkili içerik + metin isteyen görevler. `mime` bir resim türü ya da
    `application/pdf` olabilir (Gemini ikisini de doğrudan okur). Yalnızca
    metin döner."""
    from google.genai import types

    parca = types.Part.from_bytes(data=resim_bytes, mime_type=mime)
    return _uret([parca, istem], sistem, gorev)
