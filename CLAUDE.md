# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ne bu

**Aybüke** — sınıf akıllı tahtasında (Pardus/Linux, zayıf i3 işlemci)
çalışan, Gemini Live tabanlı sesli öğretmen asistanı. PyQt6 masaüstü
uygulaması, **tek başına çalışır**: sunucu, veritabanı, RAG, yerel model YOK.
Tek dış bağımlılık Gemini (canlı ses + metin/görü görevleri, aynı anahtar
havuzu). Yeni bir sunucu/servis/kütüphane eklemek kullanıcı onayı ister.

## Komutlar

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.lock.txt
./aybuke_start.sh                                   # = venv/bin/python3 main.py
venv/bin/python -c "import main"                    # temiz import kontrolü

venv/bin/python -m pytest tests/ -q                 # pytest geliştirici makinesine elle kurulur (requirements'ta YOK)
venv/bin/python -m pytest tests/test_kullanim.py -q
venv/bin/python -m pytest "tests/test_arac_kaydi.py::test_kip_kisiti_sorgulanabilir" -q
QT_QPA_PLATFORM=offscreen venv/bin/python -m pytest tests/ -q   # ekransız makinede
python tools/mikrofon_test.py --karsilastir         # tahta mikrofonu derse hazır mı
```

Testler ağsız ve modelsizdir; `tests/conftest.py` log dizinlerini
(`AYBUKE_LOG_DIR`, `AYBUKE_DERS_LOG_DIR`) geçici dizine yönlendirir — yeni
loglama bu değişkenlerin arkasında kalmalı. Offline testler Live'ın bir
ayarı kabul edip etmediğini (ses adı, model adı, config alanı) KANITLAMAZ:
bunlar değişince bir tahtada kısa gerçek bir bağlantıyla doğrula.

`requirements.lock.txt` tahtaların Python'unda (3.11) üretilir;
`requirements.txt` gerçek import kümesidir, gözle budanmaz.

## Mimari

- `main.py` — `AybukeLive`: Live oturumu, yeniden bağlanma (3→60 sn geri
  çekilme), araç dağıtımı (`_execute_tool`), ders açılışı, ders sonu.
  Oturum yalnızca **DERSİ BAŞLAT** çift tıkıyla açılır (boşta oturum para
  yakar), `BOSTA_KAPATMA_DK` (15) sessizlikte kapanır. Ders bitince süreç
  kapanmaz, bir sonraki DERSİ BAŞLAT'ı bekler.
- `ui.py` — `AybukeUI`/`MainWindow`: üç sütunlu HUD, öğretmen paneli,
  içerik paneli, kalem/silgi katmanı (yalnızca düğmeyle, model aracı değil).
- `actions/` — modelin çağırdığı araçlar. **Tek kaynak `actions/kayit.py`:**
  araç eklemek = `actions/<ad>.py` + `Arac(...)` kaydı + `_execute_tool`'da
  bir `elif`; `tests/test_arac_kaydi.py` kopmayı yakalar. `aciklama`
  metinleri modele birebir gider — kısaltmak modelin aracı çağırmayı
  bırakmasının bilinen yolu. `calisma`: `isci` (beklenir, zaman aşımlı),
  `satirici` (anında), `arkaplan` (beklenmez, araç sonucu kendisi bildirir).
  `kip`: `talimat` kipi dışlayıcıdır, normal ders araçları orada görünmez.
- `core/saglayicilar.py` — Live dışındaki metin/görü görevleri doğrudan
  Gemini'ye (`METIN_MODELI`). Başarısızlıkta `RuntimeError` yükseltir;
  çağıran bunu "uydurma, sınırlı devam et" metnine çevirir.
- `core/modeller.py` — `CANLI_MODEL`, `SES_ADI` (kadın sesi `Kore`),
  `METIN_MODELI` tek yerde.
- `core/anahtar.py` — Gemini anahtar havuzu; yalnızca kota hatasında
  sıradakine geçer (dar eşleşme bilerek). Harcama sınırı Cloud PROJESİ
  başınadır.
- `core/ders_motoru.py` — ders durum makinesi (`BEKLIYOR → YOKLAMA → … →
  BITTI`), `[DERS DURUMU]` enjeksiyonu yalnızca değişimde; öğretmen her
  zaman kazanır (`gec`, `duraklat`, `mudahale`).
- `core/zil.py`, `core/program.py` — zil çizelgesi ve ders programı
  (`config/zil.json`, `config/ders_programi.json`, gitignore'lu).
- `core/transcript.py` — ders kaydı `logs/ders/*.txt`, yalnızca metin.
- `core/kullanim.py` — Gemini token sayacı; `logs/aybuke.log`'a `TOKEN`
  satırları, ders sonunda kayda tek SİSTEM satırı. Live tur başına bir
  `usage_metadata` mesajı gönderiyor (gözlendi).
- `core/prompt.txt` — öğretmen kişiliği, **kullanıcıya ait**; istenmeden
  yeniden yazma, içine ders içeriği koyma.

## Değişmez kurallar

- **Aybüke asla dersi bozmaz.** Hiçbir araç/ölçüm hatası alım döngüsüne
  yükselmez; tam ekran hata basılmaz.
- **Kitap atfı uydurulmaz.** Elde ders kitabı metni yok; kitap sayfası
  yalnızca ekrandan (`ekrandaki_soruyu_oku`) ya da yüklenen PDF'ten
  (`file_processor`) okunur.
- Ses yapılandırması: **VAD / `realtime_input_config` ekleme** (modeli sağır
  etti), **`thinking_config` gönderme** (modeli susturdu), `language_codes`
  Live'da reddedilir. `system_instruction` ve `tools` gerçekten
  `LiveConnectConfig`'e ulaşmalı (`tests/test_oturum_yapilandirmasi.py`).
- Düşünce/araç sızıntısına karşı tek savunma `_konusma_temizle()`; yalnızca
  bilinen araç adlarını eşler.
- Kamera yok: ekran yakalama yalnızca tahtanın kendi ekranı
  (`grabWindow(0)`), kişisel veri başlıklı pencereler (`yoklama`, e-Okul,
  MEBBİS) yakalanmaz.
- `config/api_keys.json` elle düzenlenir; arayüz bu dosyaya asla yazmaz.
- Mikrofonsuz mod (`mikrofon: false`): ses girişi açılmaz, `[DEVAM]` ile
  ders kendiliğinden ilerler, `MIKSIZ_DERS_DK` (40) ya da zilden 2 dk önce
  biter. Tahta mikrofonları zayıf: seviyeyi mutlak RMS ile değil, ölçülen
  ortam sesine göre değerlendir.
- Talimat modunda (`web_ac`, `uygulama_ac`, `dosya_ac`, `pencere_kapat`)
  konuşan herkes "öğretmen" sayılır — bilinçli kabul edilmiş risk; bu
  güveni ders kiplerine genişletme.
- Son kabul testi her zaman fiziksel tahtada, kullanıcı tarafından yapılır.
