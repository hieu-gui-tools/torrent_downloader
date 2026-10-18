import os
import sys
from PySide6.QtGui import (QImage, QPainter, QColor, QLinearGradient, 
                           QPainterPath, QPen, QPolygonF)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtWidgets import QApplication

def create_icon():
    # We need a QApplication instance to use QPainter reliably in off-screen mode
    app = QApplication.instance() or QApplication(sys.argv)
    
    size = 256
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    # 1. Background rounded rectangle with modern gradient
    rect = QRectF(12, 12, 232, 232)
    gradient = QLinearGradient(12, 12, 244, 244)
    gradient.setColorAt(0.0, QColor("#1f8ef1"))  # Electric Blue
    gradient.setColorAt(0.5, QColor("#11cdef"))  # Cyan
    gradient.setColorAt(1.0, QColor("#10b981"))  # Emerald Green

    bg_path = QPainterPath()
    bg_path.addRoundedRect(rect, 52, 52)
    painter.fillPath(bg_path, gradient)

    # Subtle inner shadow / border
    border_pen = QPen(QColor(255, 255, 255, 80))
    border_pen.setWidthF(3.5)
    painter.strokePath(bg_path, border_pen)

    # 2. Draw Magnet / Signal Waves or Download Arrow
    # Draw download arrow
    arrow_color = QColor(255, 255, 255, 245)
    
    # Stem of the arrow
    stem_rect = QRectF(110, 48, 36, 68)
    stem_path = QPainterPath()
    stem_path.addRoundedRect(stem_rect, 6, 6)
    painter.fillPath(stem_path, arrow_color)

    # Head of the arrow
    arrow_head = QPolygonF([
        QPointF(70, 110),
        QPointF(186, 110),
        QPointF(128, 166)
    ])
    arrow_path = QPainterPath()
    arrow_path.addPolygon(arrow_head)
    painter.fillPath(arrow_path, arrow_color)

    # 3. Tray / Magnet base at bottom
    tray_pen = QPen(QColor(255, 255, 255, 240))
    tray_pen.setWidthF(16)
    tray_pen.setCapStyle(Qt.RoundCap)
    tray_pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(tray_pen)

    tray_path = QPainterPath()
    tray_path.moveTo(68, 165)
    tray_path.lineTo(68, 198)
    tray_path.lineTo(188, 198)
    tray_path.lineTo(188, 165)
    painter.drawPath(tray_path)

    painter.end()

    # Create assets directory
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    png_path = os.path.join(assets_dir, "app.png")
    ico_path = os.path.join(assets_dir, "app.ico")

    image.save(png_path, "PNG")
    print(f"Saved PNG to: {png_path}")

    # Save ICO format
    # Qt supports saving ICO directly
    saved_ico = image.save(ico_path, "ICO")
    if saved_ico:
        print(f"Saved ICO to: {ico_path}")
    else:
        print("Failed to save ICO directly with QImage, trying alternative...")
        import struct
        # Fallback or manual ICO creation if needed
        image.save(ico_path)

if __name__ == "__main__":
    create_icon()
