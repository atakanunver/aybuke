## 2026-10-02 - Tek başına çalışan, yalnızca Gemini kullanan mimari
- Uygulama sunucusuz kuruldu: RAG, veritabanı, yerel model ve sunucuya bağlı araçlar (kitap içeriği, kitap soru-cevap, kitap sayfası, sınav arşivi, geçmiş ders hatırlama, harici yoklama, ders kaydı yedekleme, sürüm kontrolü) yok. Dosya okuma, web arama sentezi ve YouTube özeti `core/saglayicilar.py` üzerinden doğrudan Gemini'ye (`gemini-flash-latest`) bağlandı; Word/Excel/PowerPoint okunmuyor (yerel ayrıştırma kütüphanesi eklenmedi, PDF'e yönlendirilir).
- Kitap metni olmadığı için prompt'taki "içerik yalnızca araçtan" kuralları "kitap atfı uydurma, emin değilsen doğrula, ekrandan/dosyadan okunan metin önceliklidir" ile değiştirildi.
- Canlı ses kadın sesi `Kore` (`core/modeller.py::SES_ADI`); bir tahtada gerçek bağlantıyla doğrulandı.
- Neden: tek bağımlılık, kurulumu ve bakımı tek bir tahtaya indirgemek.

## 2026-10-02 - Geçici genai istemcisi zincirlenmez
- `_istemci(...).models.generate_content(...)` zinciri "client has been closed" hatası verdi: geçici `genai.Client` istek bitmeden çöp toplanıp HTTP bağlantısını kapatıyor. İstemci bir değişkende tutulmalı. Offline testler bunu yakalamadı, yalnızca gerçek çağrı yakaladı.
