"""
actions/kayit.py — Araç kaydı (tool registry)

Bir aracın TEK kaynağı burasıdır. Gemini'ye giden bildirim (`bildirimler()`)
buradan üretilir; `main.py` artık ikinci bir liste tutmaz.

Neden: bildirim listesi ile `_execute_tool` içindeki dağıtım dalları elle
senkron tutuluyordu ve uyumu bir `grep` tek satırıyla "doğrulanıyordu". Bir
araç eklerken iki yeri birden güncellemeyi unutmak sessiz bir arıza demek:
model aracı çağırır, dağıtım tanımaz.

Kayıttaki üç alan çalışma zamanında gerçekten iş görür:

    zaman_asimi   Araç bu sürede dönmezse İPTAL EDİLİR ve modele "kaynak
                  gelmedi" yanıtı gider. Eskiden zaman aşımı hiç yoktu:
                  ölçülen 55,4 saniyelik bir araç çağrısı, alım
                  döngüsünün içinde await edildiği için bütün oturumu
                  kilitliyordu (öğrenci sesi de işlenmiyordu).
    calisma       Aracın nasıl koşturulacağı. Üç akış var:
                  "isci"     — iş parçacığında, ÇAĞRI beklenir (zaman aşımıyla)
                  "satirici" — anında, olay döngüsünde (kapanış)
                  "arkaplan" — iş parçacığında BAŞLATILIR, SONUCU BEKLENMEZ
                               (2026-09-04, gorsel_uret): model hemen bir
                               onay cümlesi alır, ders akmaya devam eder;
                               iş bitince araç kendi `speak`/`player.
                               show_image`'ıyla (ikisi de thread-safe)
                               sonucu AYRICA bildirir. `zaman_asimi` burada
                               `_isci`'nin `asyncio.wait_for`'ı tarafından
                               DEĞİL, aracın kendi iç çağrısı tarafından
                               uygulanır (bkz. gorsel_uret.py).
    kip           Hangi ders kipinde açık. "ogretmenli"/"ogretmensiz" araçları
                  hepsi iki kipte de açık. "talimat" (öğretmen talimat modu,
                  2026-08-23) AYRI ve dışlayıcı: o kipte YALNIZCA kip'i
                  "talimat" içeren araçlar model'e bildirilir — normal ders
                  araçları (web_search, gorsel_uret, ...) o kipte hiç
                  görünmez, çünkü o modda ders anlatımı YOK. `bildirimler()`
                  bu yüzden artık bir `kip` argümanı alıyor.

`aciklama` metinleri MODELE gider ve aracın NE ZAMAN çağrılacağını anlatır.
Bunları gerekmedikçe kısaltma: metni kısaltmak, modelin aracı
kendiliğinden çağırmayı bırakmasının bilinen yoludur.
"""

from dataclasses import dataclass, field

# Ders kipleri — main.py ile aynı dizeler
KIP_HEPSI = ("ogretmenli", "ogretmensiz")

# Öğretmen talimat modu (2026-08-23) — ders YOK, öğretmen tahtayı doğrudan
# sesle yönetir. KIP_HEPSI'ye bilerek DAHİL DEĞİL: bu modda
# web_search vb. hiçbir normal ders aracı görünmemeli.
KIP_TALIMAT = "talimat"


@dataclass(frozen=True)
class Arac:
    ad: str
    aciklama: str                  # modele giden metin — BİREBİR korunur
    parametreler: dict             # Gemini şeması
    izin: str                      # erişim etiketi — henüz hiçbir yerde uygulanmıyor
    maliyet: str                   # yerel | dusuk | yuksek
    zaman_asimi: float | None      # saniye; None = uygulanmaz (satırici)
    calisma: str = "isci"          # isci | satirici
    kip: tuple = KIP_HEPSI
    cikti: str = "metin"
    gereken_baglam: tuple = field(default_factory=tuple)


ARACLAR: list[Arac] = [
    Arac(
        ad="site_goster",
        aciklama=(
            "Shows content from an approved reference website on the board. "
            "Use for dictionary definitions (TDK), encyclopedia articles "
            "(Wikipedia), official curriculum pages (MEB, EBA, and its "
            "ogmmateryal.eba.gov.tr materials portal), statistics (TÜİK), "
            "weather data (MGM), history sources (TTK), and — when the "
            "teacher asks for exam-prep material (LGS/YKS topic summaries or "
            "past questions) — mebi.eba.gov.tr; note only its text/menu "
            "content comes through, not its lecture videos (this tool shows "
            "no video, see below). "
            "Give either a full URL or just a search term — a term is looked up "
            "on Turkish Wikipedia. "
            "ONLY whitelisted domains work; anything else is refused, so do not "
            "promise the class you will open an arbitrary site. This returns "
            "cleaned TEXT, not a live page: interactive content, embedded video "
            "and simulations cannot be shown this way — use youtube_video for "
            "video. Use this when the class needs a definition or a reference "
            "source."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "url":   {"type": "STRING", "description": "Full address of the approved page."},
                "arama": {"type": "STRING", "description": "Term to look up on Turkish Wikipedia if no URL is given."},
            },
            "required": [],
        },
        izin="kaynak.site",
        maliyet="dusuk",
        zaman_asimi=10.0,
        cikti="metin",
    ),
    Arac(
        ad="geogebra",
        aciklama=(
            "Opens GeoGebra on the board and drives it LIVE — the math "
            "visualisation tool for functions, graphs, geometry and 3D. Use it "
            "when a concept is clearer seen and explored than told: e.g. for "
            "quadratics create sliders a, h, k and f(x)=a(x-h)^2+k, then change "
            "a value with 'degerler' while you explain ('şimdi a'yı 3 yapıyorum, "
            "parabol nasıl değişti?'); students can also drag the sliders on "
            "the board themselves. 'komutlar' are GeoGebra input-bar commands "
            "in ENGLISH syntax, run in order: 'a=Slider(-5,5,0.1)', "
            "'f(x)=a(x-h)^2+k', 'A=(1,2)', 'c=Circle(A,3)', 'Intersect(f,g)'. "
            "Symbolic (CAS) commands — Solve, Factor, Expand, Simplify, "
            "Tangent, NSolve — work ONLY with uygulama='classic'; graphing "
            "and geometry reject them. "
            "To change an existing number use 'degerler' ([{\"ad\": \"a\", \"deger\": 2}]), not "
            "SetValue. temizle=true starts from an empty scene. The result "
            "lists any command GeoGebra rejected — fix its syntax and resend; "
            "never describe a rejected object as if it were drawn. "
            "kapat=true closes the window."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "komutlar": {"type": "ARRAY", "items": {"type": "STRING"},
                             "description": "GeoGebra commands (English syntax), executed in order."},
                "degerler": {"type": "ARRAY",
                             "items": {"type": "OBJECT", "properties": {
                                 "ad":    {"type": "STRING", "description": "Existing number/slider name, e.g. 'a'."},
                                 "deger": {"type": "NUMBER", "description": "New value."},
                             }, "required": ["ad", "deger"]},
                             "description": "Set existing numbers/sliders, e.g. [{\"ad\": \"a\", \"deger\": 2}]."},
                "temizle":  {"type": "BOOLEAN", "description": "true = clear the scene before running the commands."},
                "uygulama": {"type": "STRING", "enum": ["graphing", "geometry", "3d", "classic"],
                             "description": "GeoGebra app. Default graphing; geometry for constructions, 3d for solids, classic for symbolic/CAS commands (Solve, Factor, Tangent). Changing it reloads the scene."},
                "kapat":    {"type": "BOOLEAN", "description": "true = close the GeoGebra window."},
            },
            "required": [],
        },
        izin="arac.geogebra",
        maliyet="yerel",
        zaman_asimi=28.0,          # en kötü: 8 sn + Chrome kapatma (≤5) + 8 sn yeniden açma + 5 sn yanıt (geogebra.ILK_DENEME)
        kip=KIP_HEPSI + (KIP_TALIMAT,),
        cikti="metin",
    ),
    Arac(
        ad="file_processor",
        aciklama=(
            "Reads a document or image the teacher or student dropped onto the "
            "board. Handles PDF lecture notes and worksheets, images of "
            "handwritten work or questions, Word (.docx) and Excel (.xlsx) files, "
            "and plain-text data (txt, csv, json, xml, html). PowerPoint and old "
            ".doc/.xls files are NOT readable — ask the teacher to save them as "
            "PDF. It only reads: it cannot edit, "
            "convert or save files. "
            "ALWAYS call this when a file has been uploaded and a command is given "
            "about it. If the command is ambiguous, pick the most useful action — "
            "usually 'summarize'."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "file_path": {
                    "type": "STRING",
                    "description": "Full path to the uploaded file. Leave empty to use the currently uploaded file.",
                },
                "action": {
                    "type": "STRING",
                    "description": "summarize | extract_text | ocr | describe | analyze | stats",
                },
                "instruction": {
                    "type": "STRING",
                    "description": "Free-form instruction. E.g. 'bu konuyu lise seviyesinde özetle', 'sadece formülleri çıkar'",
                },
            },
            "required": [],
        },
        izin="dosya.oku",
        maliyet="yuksek",
        zaman_asimi=70.0,          # Gemini istemcisinin kendi 60 sn sınırı + pay
        cikti="metin",
    ),
    Arac(
        ad="web_search",
        aciklama=(
            "Searches the web. Use when the student asks about a fact, date, formula, "
            "definition, current event, or anything you are not certain about — "
            "ALWAYS prefer searching over guessing. Accuracy matters more than speed "
            "when teaching. "
            "Modes: 'search' (default), 'news' (current events for history/geography), "
            "'research' (deep comprehensive answer for a topic explanation), "
            "'compare' (side-by-side comparison of two concepts)."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Search query or topic"},
                "mode":   {"type": "STRING", "description": "search | news | research | compare"},
                "items":  {"type": "ARRAY",  "items": {"type": "STRING"}, "description": "Concepts to compare (compare mode)"},
                "aspect": {"type": "STRING", "description": "Comparison aspect"},
            },
            "required": ["query"],
        },
        izin="ag.arama",
        maliyet="yuksek",
        zaman_asimi=20.0,
        cikti="metin",
    ),
    Arac(
        ad="youtube_video",
        aciklama=(
            "Finds or summarizes educational videos. Use when a topic is easier shown "
            "than told, when the student asks for a konu anlatım video, or when they "
            "want a video they are watching summarized."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "play | summarize | get_info (default: play)"},
                "query":  {"type": "STRING", "description": "Search query for play action, e.g. 'türev konu anlatımı'"},
                "save":   {"type": "BOOLEAN", "description": "Save summary to a file (summarize only)"},
                "url":    {"type": "STRING", "description": "Video URL for summarize/get_info action"},
            },
            "required": [],
        },
        izin="ag.video",
        maliyet="yuksek",
        zaman_asimi=30.0,
        cikti="metin",
    ),
    Arac(
        ad="eba",
        aciklama=(
            "Opens EBA (Eğitim Bilişim Ağı, the official MEB education portal) "
            "content — lesson videos and question/worksheet PDFs. Use 'video' when "
            "the teacher or student wants an EBA konu anlatım video, and 'pdf' when "
            "they give an EBA link to a question sheet or document. "
            "Only eba.gov.tr links are accepted — refuses anything else. "
            "Prefer this over youtube_video specifically when EBA is named or an "
            "eba.gov.tr link is given."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "video | pdf (default: video)"},
                "query":  {"type": "STRING", "description": "Topic to search for (video action, when no direct URL is known)"},
                "url":    {"type": "STRING", "description": "Direct eba.gov.tr URL — required for pdf action, optional for video"},
            },
            "required": [],
        },
        izin="ag.video",
        maliyet="yuksek",
        zaman_asimi=30.0,
        cikti="metin",
    ),
    Arac(
        ad="web_ac",
        aciklama=(
            "ÖĞRETMEN TALİMAT MODU ONLY. Opens a REAL web browser to a site "
            "or URL — 'internet aç', 'google aç', 'eba.gov.tr aç', 'youtube "
            "aç'. Call once per single-sentence command, then confirm in "
            "ONE short sentence — do not explain, do not start teaching."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "hedef": {"type": "STRING", "description": "Site name, domain or URL, e.g. 'google', 'eba.gov.tr', 'youtube'."},
            },
            "required": ["hedef"],
        },
        izin="sistem.tarayici",
        maliyet="yerel",
        zaman_asimi=8.0,
        kip=(KIP_TALIMAT,),
        cikti="onay",
    ),
    Arac(
        ad="uygulama_ac",
        aciklama=(
            "ÖĞRETMEN TALİMAT MODU ONLY. Launches a known desktop app — "
            "'pardus kalem uygulamasını aç', 'çizim uygulamasını aç', 'dosya "
            "yöneticisini aç'. Only a small fixed set of apps is recognized; "
            "if unsure ask the teacher to name one of the known ones rather "
            "than guessing."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "uygulama": {"type": "STRING", "description": "App name as the teacher said it, e.g. 'kalem', 'çizim', 'dosya yöneticisi'."},
            },
            "required": ["uygulama"],
        },
        izin="sistem.uygulama",
        maliyet="yerel",
        zaman_asimi=8.0,
        kip=(KIP_TALIMAT,),
        cikti="onay",
    ),
    Arac(
        ad="dosya_ac",
        aciklama=(
            "ÖĞRETMEN TALİMAT MODU ONLY. Opens a folder or a specific file "
            "by name under the board's home directory — 'ev dizinini aç', "
            "'atakan.pdf dosyasını aç', '9.21.mp3 dosyasını çal'. xdg-open "
            "picks the right app (PDF viewer, media player, ...) automatically."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "hedef": {"type": "STRING", "description": "Folder keyword (e.g. 'ev dizini', 'masaüstü') or a file name (e.g. '9.21.mp3', 'atakan.pdf')."},
            },
            "required": ["hedef"],
        },
        izin="sistem.dosya",
        maliyet="yerel",
        zaman_asimi=10.0,
        kip=(KIP_TALIMAT,),
        cikti="onay",
    ),
    Arac(
        ad="pencere_kapat",
        aciklama=(
            "ÖĞRETMEN TALİMAT MODU ONLY. Closes an open window/app by matching "
            "its title — 'youtube'u kapat', 'çizim uygulamasını kapat', "
            "'tarayıcıyı kapat'. Works for anything opened by web_ac/"
            "uygulama_ac, including browser windows (title match, not process "
            "tracking — a browser tab usually hands off to an already-running "
            "browser process, so tracking the launch PID would not work)."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "hedef": {"type": "STRING", "description": "Words expected in the window's title, e.g. 'youtube', 'çizim', 'chrome'."},
            },
            "required": ["hedef"],
        },
        izin="sistem.pencere",
        maliyet="yerel",
        zaman_asimi=8.0,
        kip=(KIP_TALIMAT,),
        cikti="onay",
    ),
    Arac(
        ad="talimat_modundan_cik",
        aciklama=(
            "ÖĞRETMEN TALİMAT MODU ONLY. Exits command-only mode and returns "
            "to a normal taught lesson — 'öğretmen talimat modundan çık', "
            "'normal derse dön'. Call this ONLY on an explicit request to "
            "leave the mode, never on your own initiative."
        ),
        parametreler={"type": "OBJECT", "properties": {}},
        izin="sistem.mod",
        maliyet="yerel",
        zaman_asimi=None,
        calisma="satirici",
        kip=(KIP_TALIMAT,),
        cikti="onay",
    ),
    Arac(
        ad="ekran_goruntusu_al",
        aciklama=(
            "Takes a screenshot of the board's OWN screen (whatever is "
            "currently shown — a book page, content panel text, etc.) and "
            "adds it to the lesson log. NOT a camera — this board has no "
            "camera hardware, this only captures the on-screen display "
            "itself. Call when the teacher explicitly asks to save/log what "
            "is currently on screen, e.g. 'ekran görüntüsü al', 'bunu "
            "kaydet'."
        ),
        parametreler={"type": "OBJECT", "properties": {}},
        izin="ekran.yakala",
        maliyet="yerel",
        zaman_asimi=8.0,
        kip=KIP_HEPSI + (KIP_TALIMAT,),
        cikti="onay",
    ),
    Arac(
        ad="ekrandaki_soruyu_oku",
        aciklama=(
            "Captures the board's OWN screen (not a camera — this board has "
            "none) and sends the image DIRECTLY to you as a separate "
            "message a moment later, tagged [EKRAN] — you do NOT get it in "
            "this call's result. Call when the teacher or a student asks "
            "about 'ekrandaki soru/yazı/görsel' (e.g. a book page, something "
            "manually opened, drawn, or pasted on screen). This call returns "
            "IMMEDIATELY with a short acknowledgement — do NOT answer yet "
            "and do NOT guess what is on screen; wait for the [EKRAN] "
            "message before describing anything. If the screen shows "
            "personal/administrative data (attendance, e-Okul, MEBBİS) it "
            "will not be captured — you will be told this instead, say so "
            "plainly. This is for reading whatever is ACTUALLY on screen "
            "right now, sight-unseen."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "talimat": {"type": "STRING", "description": "What to do with what's read, e.g. 'çöz ve açıkla', 'özetle'. Defaults to reading, solving, and explaining."},
            },
            "required": [],
        },
        izin="ekran.yakala",
        maliyet="dusuk",
        # arkaplan: bu değer _isci'nin wait_for'ı tarafından UYGULANMAZ
        # (bkz. calisma="arkaplan" dokümantasyonu). Aracın kendi iç bekleme
        # sınırı: ctx event'i ~6 sn (gizleme 400 ms + grabWindow), OCR
        # yedeği (file_processor) kendi zaman aşımını
        # ayrıca uygular — bu alan yalnızca referans/dokümantasyon.
        zaman_asimi=8.0,
        calisma="arkaplan",
        kip=KIP_HEPSI + (KIP_TALIMAT,),
        cikti="metin",
    ),
    Arac(
        ad="gorsel_uret",
        aciklama=(
            "Generates a NEW educational image/diagram with AI when the "
            "lesson needs a visual that doesn't already exist (e.g. a "
            "concept better shown than described) and displays it on "
            "screen. This call returns IMMEDIATELY with a short 'preparing' "
            "acknowledgement — do NOT wait for it and do NOT say the image "
            "is on screen yet; keep teaching normally. Generation runs in "
            "the background and takes time; you will be told separately, "
            "in a later turn, once it is actually ready and shown — only "
            "then confirm it to the class. Use this only for generating "
            "something genuinely new."
        ),
        parametreler={
            "type": "OBJECT",
            "properties": {
                "konu": {"type": "STRING", "description": "What the image should show, e.g. 'hücre zarının yapısı', 'fotosentez döngüsü'."},
            },
            "required": ["konu"],
        },
        izin="gorsel.uret",
        maliyet="yuksek",
        zaman_asimi=45.0,          # gorsel_uret.py::ZAMAN_ASIMI ile aynı — _isci DEĞİL, aracın kendi çağrısı uygular
        calisma="arkaplan",
        cikti="gorsel",
    ),
    Arac(
        ad="dersi_bitir",
        aciklama=(
            "Ends the CURRENT LESSON and returns the board to its "
            "pre-lesson waiting state — the process itself stays running; "
            "the teacher presses DERSİ BAŞLAT again for the next lesson. "
            "Call this when the student says goodbye, wants to stop studying, "
            "or asks to close the app. The student can say this in ANY language."
        ),
        parametreler={"type": "OBJECT", "properties": {}},
        izin="oturum.kapat",
        maliyet="yerel",
        zaman_asimi=None,
        calisma="satirici",
        cikti="onay",
    ),
]

_HARITA = {a.ad: a for a in ARACLAR}


def bildirimler(kip: str | None = None) -> list[dict]:
    """
    Gemini'ye giden araç bildirimleri — kayıttan üretilir.

    `kip` verilmezse (main.py'nin başlangıç banner'ı / araç sayısı logu gibi
    bilgilendirme amaçlı çağrılarda) TÜM araçlar döner, filtre uygulanmaz.
    `kip` verilirse yalnızca `kip in a.kip` olan araçlar döner — oturuma
    fiilen giden liste bu şekilde hesaplanır (bkz. main.py._build_config).
    """
    return [
        {"name": a.ad, "description": a.aciklama, "parameters": a.parametreler}
        for a in ARACLAR
        if kip is None or kip in a.kip
    ]


def bul(ad: str) -> Arac | None:
    return _HARITA.get(ad)


def adlar() -> list[str]:
    return [a.ad for a in ARACLAR]


def zaman_asimi(ad: str, varsayilan: float = 15.0) -> float | None:
    a = _HARITA.get(ad)
    return varsayilan if a is None else a.zaman_asimi


def kipte_acik(ad: str, kip: str) -> bool:
    a = _HARITA.get(ad)
    return True if a is None else (kip in a.kip)
