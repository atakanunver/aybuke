"""
core/modeller.py — Gemini model adları ve ses ayarı TEK YERDE.

Model adları birden çok dosyaya dağılınca bir model emekliye ayrıldığında
hepsi birden kırılır ve derste sebebi anlaşılmayan bir sessizlik olur. Ad
tek yerde durur, değişiklik tek satırdır.

Canlı ses modeli ayrı tutulur: Live API'nin kabul ettiği ad kümesi metin
modellerinden farklıdır ve oradaki bir hata oturumun hiç açılmamasına yol
açar.
"""

# Gerçek zamanlı ses oturumu (main.py)
CANLI_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"

# Canlı oturumun sesi — Gemini'nin hazır (prebuilt) seslerinden kadın sesi.
# Diğer kadın sesleri: "Aoede", "Leda", "Zephyr". Geçersiz bir ad oturumun
# hiç açılmamasına yol açabilir; değiştirince bir tahtada kısa bir ders aç.
SES_ADI = "Kore"

# Zamansız metin/görü görevleri (core/saglayicilar.py): arama sentezi,
# video/belge özeti, ekrandaki görselin okunması. Google'ın kendi güncellediği
# takma ad — sabit bir sürüm adı emekliye ayrıldığında kırılmasın diye.
METIN_MODELI = "gemini-flash-latest"
