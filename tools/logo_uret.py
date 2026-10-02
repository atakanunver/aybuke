"""
tools/logo_uret.py — Aybüke logosunu ve pencere ikonunu üretir.

Amblem, HUD'un kendi çizim fonksiyonuyla (`ui.amblem_ciz`) çizilir; logo ile
arayüz hiçbir zaman ayrışmaz. Ekransız makinede de çalışır:

    QT_QPA_PLATFORM=offscreen venv/bin/python tools/logo_uret.py

Çıktılar: assets/aybuke-ikon.png (512x512, şeffaf), assets/aybuke-logo.png
(1600x560, gece zemin üzerinde amblem + yazı).
"""

import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from PyQt6.QtCore import QRectF, Qt  # noqa: E402
from PyQt6.QtGui import QFont, QImage, QPainter  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import ui  # noqa: E402


def _ressam(goruntu: QImage) -> QPainter:
    p = QPainter(goruntu)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    return p


def ikon(yol: Path, boyut: int = 512) -> None:
    g = QImage(boyut, boyut, QImage.Format.Format_ARGB32)
    g.fill(Qt.GlobalColor.transparent)
    p = _ressam(g)
    p.setBrush(ui.qcol(ui.C.BG))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(0, 0, boyut, boyut))
    ui.amblem_ciz(p, boyut / 2, boyut / 2, boyut * 0.40, 22.5,
                  ui.qcol(ui.C.ACC), ui.qcol(ui.C.PRI), parlaklik=0.8)
    p.end()
    g.save(str(yol))


def logo(yol: Path, w: int = 1600, h: int = 560) -> None:
    g = QImage(w, h, QImage.Format.Format_ARGB32)
    g.fill(ui.qcol(ui.C.BG))
    p = _ressam(g)
    r = h * 0.36
    ui.amblem_ciz(p, h * 0.52, h / 2, r, 22.5,
                  ui.qcol(ui.C.ACC), ui.qcol(ui.C.PRI), parlaklik=0.8)
    yazi_x = h * 1.02
    p.setPen(ui.qcol(ui.C.PRI))
    f = QFont(ui.YAZI, 1, QFont.Weight.DemiBold)
    f.setPixelSize(int(h * 0.30))
    f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 104)
    p.setFont(f)
    p.drawText(QRectF(yazi_x, h * 0.14, w - yazi_x, h * 0.46),
               Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, "Aybüke")
    p.setPen(ui.qcol(ui.C.TEXT_MED))
    f2 = QFont(ui.YAZI, 1, QFont.Weight.Light)
    f2.setPixelSize(int(h * 0.075))
    p.setFont(f2)
    p.drawText(QRectF(yazi_x + h * 0.01, h * 0.62, w - yazi_x, h * 0.14),
               Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
               "Sınıfın yapay zekâ öğretmeni")
    p.end()
    g.save(str(yol))


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    ui.yazi_tiplerini_yukle()
    hedef = KOK / "assets"
    hedef.mkdir(exist_ok=True)
    ikon(hedef / "aybuke-ikon.png")
    logo(hedef / "aybuke-logo.png")
    print("üretildi:", hedef / "aybuke-ikon.png", hedef / "aybuke-logo.png")
