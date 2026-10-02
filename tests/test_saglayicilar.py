"""
core/saglayicilar.py — doğrudan Gemini çağrısı. Ağ yok: `_istemci` sahte bir
istemciyle değiştirilir.

Sözleşme: başarıda düz metin döner; boş yanıt, hata ya da kota tükenmesi
RuntimeError YÜKSELTİR (asla boş/uydurma metin dönmez). Kota hatasında
havuzdaki sıradaki anahtarla bir kez daha denenir.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytest.importorskip("google.genai", reason="google-genai olmadan atlanır")

from core import saglayicilar as sg  # noqa: E402


class _SahteModeller:
    def __init__(self, davranislar, cagrilar):
        self._davranislar = davranislar
        self._cagrilar = cagrilar

    def generate_content(self, model, contents, config):
        self._cagrilar.append({"model": model, "contents": contents, "config": config})
        d = self._davranislar.pop(0)
        if isinstance(d, Exception):
            raise d
        return SimpleNamespace(text=d)


@pytest.fixture
def sahte(monkeypatch):
    durum = {"davranislar": [], "cagrilar": [], "anahtarlar": []}

    def _istemci(anahtar):
        durum["anahtarlar"].append(anahtar)
        return SimpleNamespace(models=_SahteModeller(durum["davranislar"], durum["cagrilar"]))

    havuz = ["k1", "k2"]
    monkeypatch.setattr(sg, "_istemci", _istemci)
    monkeypatch.setattr(sg.core_anahtar, "simdiki", lambda: havuz[0])
    monkeypatch.setattr(sg.core_anahtar, "kota_hatasi_mi",
                        lambda e: "RESOURCE_EXHAUSTED" in str(e))

    def _sonraki():
        if len(havuz) > 1:
            havuz.pop(0)
            return True
        return False

    monkeypatch.setattr(sg.core_anahtar, "sonrakine_gec", _sonraki)
    return durum


def test_basarili_metin_doner_ve_model_sabiti_kullanilir(sahte):
    sahte["davranislar"].append("  sonuç metni  ")
    assert sg.metin_uret("belge_ozet", "istem", sistem="kural") == "sonuç metni"
    cagri = sahte["cagrilar"][0]
    assert cagri["model"] == sg.METIN_MODELI
    assert cagri["contents"] == "istem"
    assert cagri["config"].system_instruction == "kural"


def test_bos_yanit_runtimeerror(sahte):
    sahte["davranislar"].append("")
    with pytest.raises(RuntimeError, match="belge_ozet"):
        sg.metin_uret("belge_ozet", "istem")


def test_genel_hata_tekrar_denemeden_runtimeerror(sahte):
    sahte["davranislar"].append(ValueError("geçersiz model"))
    with pytest.raises(RuntimeError, match="geçersiz model"):
        sg.metin_uret("arama_sentez", "istem")
    assert len(sahte["cagrilar"]) == 1


def test_kota_hatasinda_sonraki_anahtarla_bir_kez_daha(sahte):
    sahte["davranislar"] += [RuntimeError("429 RESOURCE_EXHAUSTED"), "ikinci anahtardan"]
    assert sg.metin_uret("arama_sentez", "istem") == "ikinci anahtardan"
    assert sahte["anahtarlar"] == ["k1", "k2"]


def test_gorsel_uret_ikili_parca_ve_istem_gonderir(sahte):
    sahte["davranislar"].append("görselde bir üçgen var")
    sonuc = sg.gorsel_uret("gorsel_okuma", "betimle", b"\x89PNG", "image/png")
    assert sonuc == "görselde bir üçgen var"
    parca, istem = sahte["cagrilar"][0]["contents"]
    assert istem == "betimle"
    assert parca.inline_data.mime_type == "image/png"
    assert parca.inline_data.data == b"\x89PNG"
