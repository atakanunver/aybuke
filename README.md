# Aybüke

Sınıf akıllı tahtasında çalışan, Gemini Live tabanlı sesli öğretmen asistanı.
**Tek başına çalışır:** sunucu, veritabanı, yerel model ya da RAG yoktur; tek
dış bağımlılık Gemini API'sidir.

- Canlı, çift yönlü sesli ders (Gemini Live, kadın sesi `Kore`).
- Öğretmenli / öğretmensiz ders kipleri ve sesli komutla tahta yönetimi
  (talimat modu).
- Ekran okuma; yüklenen PDF, Word, Excel ve resim okuma; web arama,
  YouTube/EBA, GeoGebra, görsel üretme.
- Ders kaydı (yalnızca metin, ses kaydı yok) ve Gemini token kullanım kaydı.

## Kurulum (Linux / Pardus tahta)

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.lock.txt
cp config/api_keys.example.json config/api_keys.json        # Gemini anahtarını ve derslik'i yaz
cp config/zil.example.json config/zil.json                  # okulun zil saatleri
cp config/ders_programi.example.json config/ders_programi.json   # isteğe bağlı
./aybuke_start.sh
```

Sistem paketleri: `libportaudio2`, `libxcb-cursor0`, `wmctrl`, `xprop`
(ekran gizlilik filtresi), Chrome/Chromium (GeoGebra ve web açma).

GeoGebra çevrimdışı paketi (~120 MB, Math Apps Bundle) repoda yoktur ve
indirilmez; `actions/geogebra.py::GEOGEBRA_YOLLARI`'ndaki yollardan birinde
(ör. `~/geogebra/bundle/GeoGebra`) kurulu olmalıdır. Okul tahtalarında
paket zaten kuruludur.

## Maliyet notu

Canlı ses oturumu ve yan görevler (dosya okuma, arama özeti, ekran okuma,
görsel üretme) **aynı Gemini anahtarını ve kotayı** paylaşır. Kullanım
`logs/aybuke.log`'daki `TOKEN` satırlarından ve her ders kaydının sonundaki
"Gemini token kullanımı" satırından izlenir.
