## 2026-10-02 - Tek başına çalışan, yalnızca Gemini kullanan mimari
- Uygulama sunucusuz kuruldu: RAG, veritabanı, yerel model ve sunucuya bağlı araçlar (kitap içeriği, kitap soru-cevap, kitap sayfası, sınav arşivi, geçmiş ders hatırlama, harici yoklama, ders kaydı yedekleme, sürüm kontrolü) yok. Dosya okuma, web arama sentezi ve YouTube özeti `core/saglayicilar.py` üzerinden doğrudan Gemini'ye (`gemini-flash-latest`) bağlandı; Word/Excel/PowerPoint okunmuyor (yerel ayrıştırma kütüphanesi eklenmedi, PDF'e yönlendirilir).
- Kitap metni olmadığı için prompt'taki "içerik yalnızca araçtan" kuralları "kitap atfı uydurma, emin değilsen doğrula, ekrandan/dosyadan okunan metin önceliklidir" ile değiştirildi.
- Canlı ses kadın sesi `Kore` (`core/modeller.py::SES_ADI`); bir tahtada gerçek bağlantıyla doğrulandı.
- Neden: tek bağımlılık, kurulumu ve bakımı tek bir tahtaya indirgemek.

## 2026-10-02 - Geçici genai istemcisi zincirlenmez
- `_istemci(...).models.generate_content(...)` zinciri "client has been closed" hatası verdi: geçici `genai.Client` istek bitmeden çöp toplanıp HTTP bağlantısını kapatıyor. İstemci bir değişkende tutulmalı. Offline testler bunu yakalamadı, yalnızca gerçek çağrı yakaladı.

## 2026-10-02 - Live maliyet tedbirleri
- Kayan pencere bağlam sıkıştırma (tetik 40 bin, hedef 24 bin token; iki kipte de), boşta kapanma 15 → 8 dk, modele giden ekran görüntüsü 1024 → 768 px (JPEG q65), mikrofonsuz [DEVAM] beklemesi 2,5 → 4 sn (boş tur 10 → 20 sn) ve [DEVAM] metni modelden daha uzun, bütünlüklü bölümler istiyor (daha az tur).
- Ölçüm (fenlab, gerçek oturum): ilk turda sabit yük 14.342 token (prompt + araç tanımları); Live tur başına tek bir usage_metadata mesajı gönderiyor.
- Neden: Live her turda tüm bağlamı yeniden işleyip faturalıyor; maliyet bağlam boyu × tur sayısı ile büyüyor. Etkisi TOKEN satırlarıyla (en_buyuk_baglam, mesaj sayısı) ölçülecek.
