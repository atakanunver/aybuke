"""
Araç kaydı — bildirim ve dağıtım tek kaynaktan gelmeli.

Kayıt ile main.py'deki dağıtım dalları birbirinden kopmamalı.
"""

import re
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from actions import kayit                      # noqa: E402


def test_bildirim_sayisi_kayitla_ayni():
    assert len(kayit.bildirimler()) == len(kayit.ARACLAR)


def test_bildirimler_gemini_semasina_uyar():
    for b in kayit.bildirimler():
        assert b["name"] and b["description"]
        assert b["parameters"]["type"] == "OBJECT"
        for zorunlu in b["parameters"].get("required", []):
            assert zorunlu in b["parameters"]["properties"], \
                f"{b['name']}: required alan properties içinde yok: {zorunlu}"


def test_dagitim_dallari_kayitla_ortusuyor():
    """main.py içindeki `name == "..."` dalları ile kayıt aynı olmalı."""
    kaynak = (KOK / "main.py").read_text(encoding="utf-8")
    dagitim = set(re.findall(r'name == "(\w+)"', kaynak))
    assert dagitim == set(kayit.adlar())


@pytest.mark.parametrize("arac", kayit.ARACLAR, ids=lambda a: a.ad)
def test_agir_araclarin_zaman_asimi_var(arac):
    """
    İş parçacığında çalışan her aracın zaman aşımı OLMAK ZORUNDA.

    Zaman aşımı yokken ölçülen 55,4 saniyelik bir çağrı, alım döngüsünün
    içinde await edildiği için bütün oturumu kilitliyordu.
    """
    if arac.calisma in ("isci", "arkaplan"):
        # "isci": zaman_asimi `_isci`'nin `asyncio.wait_for`'ı tarafından
        # uygulanır. "arkaplan" (2026-09-04, gorsel_uret): ÇAĞRI
        # beklenmediği için `_isci` devrede değil, ama aracın kendi iç
        # çağrısı hâlâ bir üst sınıra ihtiyaç duyar — yoksa yanıt vermeyen
        # bir sağlayıcı çağrısı iş parçacığında süresiz asılı kalır.
        assert arac.zaman_asimi and arac.zaman_asimi > 0
    else:
        # satirici (anında) akışında zaman aşımı uygulanmaz; bunu açıkça
        # belirtmek gerekir.
        assert arac.zaman_asimi is None


@pytest.mark.parametrize("arac", kayit.ARACLAR, ids=lambda a: a.ad)
def test_her_aracin_izni_ve_maliyet_sinifi_var(arac):
    assert arac.izin
    assert arac.maliyet in ("yerel", "dusuk", "yuksek")


def test_kip_kisiti_sorgulanabilir():
    assert kayit.kipte_acik("web_search", "ogretmenli")
    assert kayit.kipte_acik("web_search", "ogretmensiz")
    assert not kayit.kipte_acik("web_search", "talimat")


def test_dersi_bitir_aciklamasi_surec_kapaniyor_demiyor():
    """2026-09-01: dersi_bitir artık süreci öldürmüyor (bkz. _DersBitti)
    — yalnızca dersi bitirip DERSİ BAŞLAT öncesi bekleme durumuna dönüyor.
    Modelin yanlış bir "kapanıyor"/"asistan tamamen kapanıyor" iddiasında
    bulunması, web_ac(hedef='kapat') ile aynı
    sınıftan bir hataydı — açıklama metni bunu artık söylememeli."""
    arac = kayit._HARITA["dersi_bitir"]
    assert "closes the assistant completely" not in arac.aciklama


def test_sunucuya_bagli_araclar_kayitta_yok():
    """Uygulama tek başına çalışır: kitap/sınav arşivi, geçmiş ders ve dış
    yoklama araçları yok. Modele var olmayan bir araç bildirilirse model onu
    çağırıyormuş gibi anlatır."""
    for ad in ("ders_icerigi", "kitap_sorusu", "pdf_sayfa", "yks_sorulari",
               "ders_hafizasi", "yoklama_al"):
        assert ad not in kayit.adlar()
