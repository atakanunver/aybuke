"""
actions/file_processor.py — dosya türüne göre doğru Gemini yolu seçilir,
desteklenmeyen türler ve hatalar uydurma metne değil açık bir yönlendirmeye
dönüşür. Ağ yok: `saglayicilar` sahte fonksiyonlarla değiştirilir.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from actions import file_processor as fp  # noqa: E402


@pytest.fixture
def cagrilar(monkeypatch):
    kayit = []
    monkeypatch.setattr(fp.saglayicilar, "gorsel_uret",
                        lambda gorev, istem, veri, mime, sistem=None:
                        kayit.append(("gorsel", gorev, mime, istem)) or "ikili-sonuc")
    monkeypatch.setattr(fp.saglayicilar, "metin_uret",
                        lambda gorev, istem, sistem=None:
                        kayit.append(("metin", gorev, istem)) or "metin-sonuc")
    return kayit


def test_pdf_ikili_olarak_gider(tmp_path, cagrilar):
    f = tmp_path / "not.pdf"
    f.write_bytes(b"%PDF-1.4")
    assert fp.file_processor({"file_path": str(f), "action": "summarize"}) == "ikili-sonuc"
    assert cagrilar[0][:3] == ("gorsel", "belge_ozet", "application/pdf")


def test_resim_ocr_istemiyle_gider(tmp_path, cagrilar):
    f = tmp_path / "soru.JPG"
    f.write_bytes(b"\xff\xd8")
    fp.file_processor({"file_path": str(f), "action": "ocr", "instruction": "formülleri ayır"})
    tur, gorev, mime, istem = cagrilar[0]
    assert (tur, mime) == ("gorsel", "image/jpeg")
    assert "formülleri ayır" in istem


def test_metin_dosyasi_icerikle_birlikte_metin_olarak_gider(tmp_path, cagrilar):
    f = tmp_path / "veri.csv"
    f.write_text("ad,not\nAli,90\n", encoding="utf-8")
    assert fp.file_processor({"file_path": str(f), "action": "analyze"}) == "metin-sonuc"
    assert "Ali,90" in cagrilar[0][2]


def test_word_paragraf_ve_tablo_metni_gider(tmp_path, cagrilar):
    docx = pytest.importorskip("docx")
    belge = docx.Document()
    belge.add_paragraph("Fotosentez ışık enerjisi gerektirir.")
    tablo = belge.add_table(rows=1, cols=2)
    tablo.rows[0].cells[0].text = "Klorofil"
    tablo.rows[0].cells[1].text = "Yeşil pigment"
    f = tmp_path / "not.docx"
    belge.save(str(f))
    assert fp.file_processor({"file_path": str(f)}) == "metin-sonuc"
    istem = cagrilar[0][2]
    assert "Fotosentez ışık enerjisi" in istem
    assert "Klorofil | Yeşil pigment" in istem


def test_excel_tum_sayfalar_ve_hesaplanmis_degerler_gider(tmp_path, cagrilar):
    openpyxl = pytest.importorskip("openpyxl")
    kitap = openpyxl.Workbook()
    kitap.active.title = "9-A"
    kitap.active.append(["Ad", "Not"])
    kitap.active.append(["Ayşe", 85])
    ikinci = kitap.create_sheet("9-B")
    ikinci.append(["Mehmet", 70])
    f = tmp_path / "notlar.xlsx"
    kitap.save(str(f))
    fp.file_processor({"file_path": str(f), "action": "stats"})
    istem = cagrilar[0][2]
    assert "[Sayfa: 9-A]" in istem and "[Sayfa: 9-B]" in istem
    assert "Ayşe\t85" in istem and "Mehmet\t70" in istem


def test_bozuk_word_dosyasi_uydurmayi_engelleyen_metne_doner(tmp_path, cagrilar):
    pytest.importorskip("docx")
    f = tmp_path / "bozuk.docx"
    f.write_bytes(b"PK bozuk")
    assert "açılamadı" in fp.file_processor({"file_path": str(f)})
    assert cagrilar == []


@pytest.mark.parametrize("ad", ["sunum.pptx", "eski.doc", "eski.xls"])
def test_desteklenmeyen_ofis_dosyasi_pdf_yonlendirmesi_doner(tmp_path, cagrilar, ad):
    f = tmp_path / ad
    f.write_bytes(b"x")
    assert "PDF" in fp.file_processor({"file_path": str(f)})
    assert cagrilar == []


def test_gemini_hatasi_uydurmayi_engelleyen_metne_doner(tmp_path, monkeypatch):
    def _patla(*a, **k):
        raise RuntimeError("kota")
    monkeypatch.setattr(fp.saglayicilar, "gorsel_uret", _patla)
    f = tmp_path / "a.pdf"
    f.write_bytes(b"%PDF")
    assert "tahmin yürütme" in fp.file_processor({"file_path": str(f)})


def test_cok_buyuk_dosya_reddedilir(tmp_path, monkeypatch, cagrilar):
    monkeypatch.setattr(fp, "AZAMI_BOYUT", 3)
    f = tmp_path / "b.pdf"
    f.write_bytes(b"%PDF-1.4")
    assert "çok büyük" in fp.file_processor({"file_path": str(f)})
    assert cagrilar == []
