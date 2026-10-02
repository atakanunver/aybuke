"""
main.py::AybukeLive._on_ders_bitir() — DERSİ BİTİR düğmesinin (ui.py) çift
tıkına bağlanan köprü. Öğretmen mikrofon modu/talimat modu değiştirmek için
40 dakika beklemeden ya da tahtayı yeniden başlatmadan dersi bitirebilsin
diye eklendi.

Ağ yok — `_dersi_bitir` mock'lanır, yalnızca `asyncio.run_coroutine_threadsafe`
ile gerçek loop'a doğru zamanlandığı doğrulanır (aynı desen:
tests/test_durdur_zorlama.py).
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytest.importorskip("sounddevice", reason="ses bağımlılıkları olmadan atlanır")

import main  # noqa: E402


def _aybuke_live(loop, ders_suruyor: bool, bitmekte: bool = False) -> main.AybukeLive:
    f = main.AybukeLive.__new__(main.AybukeLive)
    f._loop = loop
    f._oturum_izni = asyncio.Event()
    if ders_suruyor:
        f._oturum_izni.set()
    f._ders_bitti_istendi = bitmekte
    return f


def _bitir_ve_topla(ders_suruyor: bool, bitmekte: bool = False) -> list:
    async def _calistir():
        f = _aybuke_live(asyncio.get_running_loop(), ders_suruyor, bitmekte)
        cagrilar = []

        async def _sahte_dersi_bitir(sebep):
            cagrilar.append(sebep)

        f._dersi_bitir = _sahte_dersi_bitir
        f._on_ders_bitir()
        await asyncio.sleep(0.05)
        return cagrilar

    return asyncio.run(_calistir())


class TestOnDersBitir:
    def test_ders_surerken_dersi_bitir_planlanir(self):
        assert _bitir_ve_topla(ders_suruyor=True) == ["öğretmen dersi bitirdi"]

    def test_loop_yokken_sessiz_kalir(self):
        f = _aybuke_live(None, ders_suruyor=False)
        f._on_ders_bitir()   # exception atmamalı

    def test_ders_yokken_sessiz_kalir(self):
        # Dersler arasında `_oturum_izni` temizdir (run()'ın ders-bitti dalı).
        assert _bitir_ve_topla(ders_suruyor=False) == []

    def test_ders_zaten_bitmekteyken_ikinci_kez_bitirmez(self):
        # Zil/boşta kalma dersi bitirirken öğretmen de çift tıkladıysa
        # `_dersi_bitir` İKİNCİ kez çalışmamalı: bayrak bayat kalır ve bir
        # sonraki ders açılır açılmaz kapanırdı.
        assert _bitir_ve_topla(ders_suruyor=True, bitmekte=True) == []


class TestYenidenBaglanirkenBitir:
    def test_bayrak_acikken_run_baglanmadan_dersi_bitirir(self):
        # Bağlantı koptuğu sırada DERSİ BİTİR'e basıldıysa run() yeni
        # bağlantı açmadan ders-bitti dalına gitmeli (istek kaybolmamalı).
        import inspect
        kaynak = inspect.getsource(main.AybukeLive.run)
        once = kaynak.index("if self._ders_bitti_istendi:\n")
        baglan = kaynak.index("client.aio.live.connect")
        assert once < baglan
        assert "raise _DersBitti()" in kaynak[once:baglan]


class TestDersiBitirTekrarGirisi:
    def test_ayni_anda_iki_bitirme_tek_kapanis_yapar(self, monkeypatch):
        # Zil/boşta kalma/mikrofonsuz süre ile öğretmenin DERSİ BİTİR'i aynı
        # anda gelirse ikinci `_dersi_bitir` girmemeli: çift kapanış satırı
        # ve bayat `_ders_bitti_istendi` (sonraki dersi açılır açılmaz kapatır).
        kapanis = []
        monkeypatch.setattr(main.transcript, "log_line", lambda *a, **k: None)
        monkeypatch.setattr(main.transcript, "log_session_end",
                            lambda: kapanis.append(1))

        async def _calistir():
            f = main.AybukeLive.__new__(main.AybukeLive)
            f._ders_bitti_istendi = False
            f._ders_bitti_event = asyncio.Event()
            await asyncio.gather(f._dersi_bitir("zil"),
                                 f._dersi_bitir("öğretmen dersi bitirdi"))
            return f

        f = asyncio.run(_calistir())
        assert kapanis == [1]
        assert f._ders_bitti_istendi is True
        assert f._ders_bitti_event.is_set()
