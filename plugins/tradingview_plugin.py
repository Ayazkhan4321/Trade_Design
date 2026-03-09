"""
Trading Chart Plugin for PySide6
=================================
- Candlestick chart with historical data from Binance REST API
- Live data via Binance WebSocket
- Designed as a left-panel plugin widget
- Supports multiple timeframes and symbols
"""

import sys
import json
import time
import asyncio
import threading
import urllib.request
from datetime import datetime
from collections import deque
from services.api_Client import ApiClient


from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QSplitter, QFrame, QSizePolicy,
    QScrollArea, QListWidget, QListWidgetItem, QStatusBar, QToolBar,
    QSpinBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QPointF, QRectF, QRect, Slot
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QLinearGradient, QFontMetrics, QIcon, QPixmap, QAction
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QUrl

try:
    from PySide6.QtWebSockets import QWebSocket
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


# ─────────────────────────── THEME ───────────────────────────
class Theme:
    BG_DARK       = QColor("#0d1117")
    BG_PANEL      = QColor("#161b22")
    BG_CARD       = QColor("#1c2128")
    BG_HOVER      = QColor("#21262d")
    BORDER        = QColor("#30363d")
    ACCENT        = QColor("#58a6ff")
    ACCENT2       = QColor("#388bfd")
    GREEN         = QColor("#3fb950")
    GREEN_DIM     = QColor("#1a4a22")
    RED           = QColor("#f85149")
    RED_DIM       = QColor("#4a1a1a")
    YELLOW        = QColor("#d29922")
    TEXT_PRIMARY  = QColor("#e6edf3")
    TEXT_SECONDARY= QColor("#8b949e")
    TEXT_MUTED    = QColor("#484f58")
    GRID          = QColor("#21262d")
    WICK          = QColor("#6e7681")


# ─────────────────────────── DATA CLASSES ───────────────────────────
class Candle:
    __slots__ = ("time", "open", "high", "low", "close", "volume")

    def __init__(self, time, open_, high, low, close, volume):
        self.time   = time
        self.open   = float(open_)
        self.high   = float(high)
        self.low    = float(low)
        self.close  = float(close)
        self.volume = float(volume)

    @property
    def bullish(self):
        return self.close >= self.open

    @property
    def body_size(self):
        return abs(self.close - self.open)

    @property
    def range(self):
        return self.high - self.low


# ─────────────────────────── API WORKER ───────────────────────────
class HistoricalDataWorker(QThread):
    data_ready = Signal(list)
    error = Signal(str)

    def __init__(self, symbol, interval, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.interval = interval
        self.api = ApiClient()

    def run(self):
        try:
            # Convert UI interval like "1m" → "1"
            interval_value = self.interval.replace("m", "").replace("h", "").replace("d", "")
    
            data = self.api.get_aggs(
                symbol=self.symbol,
                start="2026-02-01",
                end="2026-03-03",
                interval=interval_value
            )
    
            if not data or "results" not in data:
                self.error.emit("No data received")
                return
    
            candles = []
            for d in data["results"]:
                candles.append(
                    Candle(
                        time=int(d["t"]) // 1000,
                        open_=d["o"],
                        high=d["h"],
                        low=d["l"],
                        close=d["c"],
                        volume=d["v"],
                    )
                )
    
            self.data_ready.emit(candles)
    
        except Exception as e:
            self.error.emit(str(e))

# ─────────────────────────── WEBSOCKET WORKER ───────────────────────────


# ─────────────────────────── CANDLE CHART WIDGET ───────────────────────────
class CandleChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.candles: list[Candle] = []
        self.live_candle: Candle | None = None

        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # View params
        self._offset        = 0      # candles scrolled from right
        self._visible_count = 80
        self._candle_gap    = 0.15   # fraction of candle width as gap
        self._padding       = {"top": 20, "bottom": 60, "left": 10, "right": 80}

        self._hover_idx = -1
        self.setMouseTracking(True)
    
    
        # ── public API ──────────────────────────────────────────────
    def set_candles(self, candles: list[Candle]):
        self.candles = candles
        self.live_candle = None
        self._offset = 0
        self.update()



    def update_live(self, data: dict):
        c = Candle(data["time"], data["open"], data["high"],
                   data["low"], data["close"], data["volume"])
        if self.candles and self.candles[-1].time == c.time:
            self.candles[-1] = c
        else:
            if data.get("closed") and self.candles:
                self.candles.append(c)
                if len(self.candles) > 500:
                    self.candles.pop(0)
            else:
                self.live_candle = c
        self.update()

    # ── geometry helpers ────────────────────────────────────────
    def _chart_rect(self) -> QRectF:
        p = self._padding
        return QRectF(
            p["left"], p["top"],
            self.width() - p["left"] - p["right"],
            self.height() - p["top"] - p["bottom"]
        )

    def _visible_candles(self):
        all_c = self.candles[:]
        if self.live_candle:
            all_c = all_c + [self.live_candle]
        start = max(0, len(all_c) - self._visible_count - self._offset)
        end   = max(0, len(all_c) - self._offset)
        return all_c[start:end]

    def _price_range(self, visible):
        if not visible:
            return 0, 1
        lo = min(c.low  for c in visible)
        hi = max(c.high for c in visible)
        margin = (hi - lo) * 0.05 or hi * 0.01
        return lo - margin, hi + margin

    def _price_to_y(self, price, lo, hi, rect: QRectF) -> float:
        if hi == lo:
            return rect.center().y()
        return rect.bottom() - (price - lo) / (hi - lo) * rect.height()

    def _candle_x(self, idx: int, count: int, rect: QRectF):
        """Return (x_center, candle_width) for candle at position idx."""
        w = rect.width() / max(count, 1)
        gap = w * self._candle_gap
        body_w = max(w - gap, 1)
        cx = rect.left() + (idx + 0.5) * w
        return cx, body_w

    # ── painting ────────────────────────────────────────────────
    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self._draw_background(painter)
        visible = self._visible_candles()
        if not visible:
            self._draw_empty(painter)
            painter.end()
            return

        rect = self._chart_rect()
        lo, hi = self._price_range(visible)

        self._draw_grid(painter, rect, lo, hi)
        self._draw_volume(painter, rect, visible)
        self._draw_candles(painter, rect, visible, lo, hi)
        self._draw_price_axis(painter, rect, lo, hi)
        self._draw_time_axis(painter, rect, visible)
        if self._hover_idx >= 0 and self._hover_idx < len(visible):
            self._draw_crosshair(painter, rect, visible, lo, hi)
            self._draw_tooltip(painter, rect, visible, lo, hi)

        painter.end()

    def _draw_background(self, painter: QPainter):
        painter.fillRect(self.rect(), Theme.BG_DARK)

    def _draw_empty(self, painter: QPainter):
        painter.setPen(Theme.TEXT_MUTED)
        painter.setFont(QFont("Segoe UI", 14))
        painter.drawText(self.rect(), Qt.AlignCenter, "Loading chart data…")

    def _draw_grid(self, painter: QPainter, rect: QRectF, lo: float, hi: float):
        pen = QPen(Theme.GRID)
        pen.setStyle(Qt.DotLine)
        pen.setWidthF(0.5)
        painter.setPen(pen)

        levels = 6
        for i in range(levels + 1):
            price = lo + (hi - lo) * i / levels
            y = self._price_to_y(price, lo, hi, rect)
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

    def _draw_volume(self, painter: QPainter, rect: QRectF, visible):
        if not visible:
            return
        vol_h   = rect.height() * 0.15
        max_vol = max(c.volume for c in visible) or 1
        count   = len(visible)

        for i, c in enumerate(visible):
            cx, bw = self._candle_x(i, count, rect)
            bar_h  = (c.volume / max_vol) * vol_h
            color  = Theme.GREEN_DIM if c.bullish else Theme.RED_DIM
            painter.fillRect(
                QRectF(cx - bw / 2, rect.bottom() - bar_h, bw, bar_h),
                QBrush(color)
            )

    def _draw_candles(self, painter: QPainter, rect: QRectF, visible, lo: float, hi: float):
        count = len(visible)
        for i, c in enumerate(visible):
            cx, bw = self._candle_x(i, count, rect)
            color  = Theme.GREEN if c.bullish else Theme.RED

            # Wick
            wick_pen = QPen(color if bw > 3 else Theme.WICK)
            wick_pen.setWidthF(1.0)
            painter.setPen(wick_pen)
            y_high = self._price_to_y(c.high,  lo, hi, rect)
            y_low  = self._price_to_y(c.low,   lo, hi, rect)
            painter.drawLine(QPointF(cx, y_high), QPointF(cx, y_low))

            # Body
            y_open  = self._price_to_y(c.open,  lo, hi, rect)
            y_close = self._price_to_y(c.close, lo, hi, rect)
            body_top = min(y_open, y_close)
            body_h   = max(abs(y_close - y_open), 1.5)

            painter.fillRect(QRectF(cx - bw / 2, body_top, bw, body_h), QBrush(color))

            # Live candle outline
            if self.live_candle and i == count - 1 and c is self.live_candle:
                outline = QPen(color)
                outline.setWidthF(1.0)
                outline.setStyle(Qt.DashLine)
                painter.setPen(outline)
                painter.drawRect(QRectF(cx - bw / 2, body_top, bw, body_h))

    def _draw_price_axis(self, painter: QPainter, rect: QRectF, lo: float, hi: float):
        painter.setFont(QFont("Consolas", 9))
        painter.setPen(Theme.TEXT_SECONDARY)
        levels = 6
        for i in range(levels + 1):
            price = lo + (hi - lo) * i / levels
            y     = self._price_to_y(price, lo, hi, rect)
            label = f"{price:,.2f}"
            painter.drawText(
                QRectF(rect.right() + 4, y - 8, 76, 16),
                Qt.AlignLeft | Qt.AlignVCenter,
                label
            )

    def _draw_time_axis(self, painter: QPainter, rect: QRectF, visible):
        if not visible:
            return
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(Theme.TEXT_MUTED)
        count  = len(visible)
        step   = max(1, count // 8)
        for i in range(0, count, step):
            c  = visible[i]
            cx, _ = self._candle_x(i, count, rect)
            ts = datetime.fromtimestamp(c.time).strftime("%H:%M\n%m/%d")
            painter.drawText(
                QRectF(cx - 25, rect.bottom() + 4, 50, 40),
                Qt.AlignHCenter | Qt.AlignTop,
                ts
            )

    def _draw_crosshair(self, painter: QPainter, rect: QRectF, visible, lo: float, hi: float):
        i  = self._hover_idx
        c  = visible[i]
        cx, _ = self._candle_x(i, len(visible), rect)
        cy = self._price_to_y(c.close, lo, hi, rect)

        pen = QPen(Theme.TEXT_MUTED)
        pen.setStyle(Qt.DashLine)
        pen.setWidthF(0.8)
        painter.setPen(pen)
        painter.drawLine(QPointF(cx, rect.top()), QPointF(cx, rect.bottom()))
        painter.drawLine(QPointF(rect.left(), cy), QPointF(rect.right(), cy))

        # Price tag on axis
        tag_color = Theme.GREEN if c.bullish else Theme.RED
        painter.fillRect(QRectF(rect.right() + 2, cy - 9, 78, 18), QBrush(tag_color))
        painter.setPen(Theme.BG_DARK)
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(
            QRectF(rect.right() + 2, cy - 9, 78, 18),
            Qt.AlignCenter,
            f"{c.close:,.2f}"
        )

    def _draw_tooltip(self, painter: QPainter, rect: QRectF, visible, lo: float, hi: float):
        i = self._hover_idx
        c = visible[i]
        color = Theme.GREEN if c.bullish else Theme.RED
        chg   = c.close - c.open
        chg_p = (chg / c.open * 100) if c.open else 0

        ts    = datetime.fromtimestamp(c.time).strftime("%Y-%m-%d %H:%M")
        lines = [
            ("Date",   ts),
            ("O",      f"{c.open:,.4f}"),
            ("H",      f"{c.high:,.4f}"),
            ("L",      f"{c.low:,.4f}"),
            ("C",      f"{c.close:,.4f}"),
            ("Chg",    f"{chg:+.4f} ({chg_p:+.2f}%)"),
            ("Vol",    f"{c.volume:,.2f}"),
        ]

        fw, fh = 175, len(lines) * 18 + 14
        tx = rect.left() + 8
        ty = rect.top() + 8

        painter.setRenderHint(QPainter.Antialiasing)
        bg_rect = QRectF(tx, ty, fw, fh)
        painter.fillRect(bg_rect, QBrush(QColor("#1c2128ee")))
        border_pen = QPen(Theme.BORDER)
        border_pen.setWidthF(1)
        painter.setPen(border_pen)
        painter.drawRect(bg_rect)

        painter.setFont(QFont("Consolas", 8))
        for row, (k, v) in enumerate(lines):
            ry = ty + 8 + row * 18
            painter.setPen(Theme.TEXT_MUTED)
            painter.drawText(QRectF(tx + 6, ry, 32, 16), Qt.AlignLeft, k)
            clr = color if k in ("C", "Chg") else Theme.TEXT_PRIMARY
            painter.setPen(clr)
            painter.drawText(QRectF(tx + 42, ry, fw - 48, 16), Qt.AlignLeft, v)

    # ── mouse events ────────────────────────────────────────────
    def mouseMoveEvent(self, event):
        rect    = self._chart_rect()
        visible = self._visible_candles()
        if not visible or not rect.contains(event.position()):
            self._hover_idx = -1
            self.update()
            return
        count   = len(visible)
        rel_x   = event.position().x() - rect.left()
        cw      = rect.width() / max(count, 1)
        idx     = int(rel_x / cw)
        self._hover_idx = max(0, min(idx, count - 1))
        self.update()

    def leaveEvent(self, _event):
        self._hover_idx = -1
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self._visible_count = max(20,  self._visible_count - 5)
        else:
            self._visible_count = min(300, self._visible_count + 5)
        self.update()


# ─────────────────────────── PLUGIN PANEL ───────────────────────────
class TradingChartPlugin(QWidget):
    """
    Self-contained plugin widget — drop it into any QSplitter or layout.
    """

    SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD"]
    INTERVALS  = ["1m", "5m", "15m", "1h", "4h", "1d"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(500)
        self._api_worker: HistoricalDataWorker | None = None

        self._build_ui()
        self._connect_signals()
        self._load_data()

    # ── UI construction ─────────────────────────────────────────
    def _build_ui(self):
        self.setStyleSheet(f"""
            QWidget {{ background: {Theme.BG_DARK.name()}; color: {Theme.TEXT_PRIMARY.name()}; }}
            QComboBox, QPushButton {{
                background: {Theme.BG_CARD.name()};
                border: 1px solid {Theme.BORDER.name()};
                border-radius: 4px;
                padding: 4px 10px;
                color: {Theme.TEXT_PRIMARY.name()};
                font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox:hover, QPushButton:hover {{
                background: {Theme.BG_HOVER.name()};
                border-color: {Theme.ACCENT.name()};
            }}
            QPushButton:pressed {{ background: {Theme.ACCENT2.name()}; }}
            QLabel {{ background: transparent; }}
            QStatusBar {{ background: {Theme.BG_PANEL.name()}; border-top: 1px solid {Theme.BORDER.name()}; }}
        """)

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header bar ───────────────────────────────────
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet(
            f"background:{Theme.BG_PANEL.name()}; border-bottom:1px solid {Theme.BORDER.name()};"
        )
        hbox = QHBoxLayout(header)
        hbox.setContentsMargins(12, 0, 12, 0)
        hbox.setSpacing(10)

        # Plugin label
        lbl_plugin = QLabel("📊")
        lbl_plugin.setFont(QFont("Segoe UI Emoji", 16))
        hbox.addWidget(lbl_plugin)

        title = QLabel("Trading Chart")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet(f"color:{Theme.ACCENT.name()};")
        hbox.addWidget(title)

        hbox.addStretch()

        # Symbol selector
        self.sym_cb = QComboBox()
        self.sym_cb.addItems(self.SYMBOLS)
        self.sym_cb.setFixedWidth(110)
        hbox.addWidget(self.sym_cb)

        # Interval selector
        self.intv_cb = QComboBox()
        self.intv_cb.addItems(self.INTERVALS)
        self.intv_cb.setCurrentText("1m")
        self.intv_cb.setFixedWidth(65)
        hbox.addWidget(self.intv_cb)

        # Refresh button
        self.btn_refresh = QPushButton("⟳ Load")
        self.btn_refresh.setFixedWidth(72)
        hbox.addWidget(self.btn_refresh)

        root.addWidget(header)

        # ── Stats bar ────────────────────────────────────
        stats_frame = QFrame()
        stats_frame.setFixedHeight(34)
        stats_frame.setStyleSheet(
            f"background:{Theme.BG_PANEL.name()}; border-bottom:1px solid {Theme.BORDER.name()};"
        )
        sbox = QHBoxLayout(stats_frame)
        sbox.setContentsMargins(14, 0, 14, 0)
        sbox.setSpacing(24)

        def stat_label(tag, val="—"):
            lbl_t = QLabel(tag)
            lbl_t.setFont(QFont("Segoe UI", 8))
            lbl_t.setStyleSheet(f"color:{Theme.TEXT_MUTED.name()};")
            lbl_v = QLabel(val)
            lbl_v.setFont(QFont("Consolas", 9, QFont.Bold))
            lbl_v.setStyleSheet(f"color:{Theme.TEXT_PRIMARY.name()};")
            sbox.addWidget(lbl_t)
            sbox.addWidget(lbl_v)
            return lbl_v

        self._lbl_price  = stat_label("PRICE")
        self._lbl_change = stat_label("24H CHG")
        self._lbl_high   = stat_label("HIGH")
        self._lbl_low    = stat_label("LOW")
        self._lbl_vol    = stat_label("VOL")
        sbox.addStretch()

        # WS status dot
        self._ws_dot = QLabel("●")
        self._ws_dot.setFont(QFont("Segoe UI", 10))
        self._ws_dot.setStyleSheet(f"color:{Theme.TEXT_MUTED.name()};")
        self._ws_dot.setToolTip("WebSocket status")
        sbox.addWidget(self._ws_dot)

        root.addWidget(stats_frame)

        # ── Chart ─────────────────────────────────────────
        self.chart = CandleChartWidget()
        root.addWidget(self.chart, stretch=1)

        # ── Status bar ───────────────────────────────────
        self._status = QLabel("  Ready")
        self._status.setFixedHeight(22)
        self._status.setFont(QFont("Segoe UI", 8))
        self._status.setStyleSheet(
            f"color:{Theme.TEXT_SECONDARY.name()}; "
            f"background:{Theme.BG_PANEL.name()}; "
            f"border-top:1px solid {Theme.BORDER.name()}; "
            f"padding-left:8px;"
        )
        root.addWidget(self._status)

    # ── signals ─────────────────────────────────────────────────
    def _connect_signals(self):
        self.btn_refresh.clicked.connect(self._load_data)
        self.sym_cb.currentTextChanged.connect(self._on_symbol_changed)
        self.intv_cb.currentTextChanged.connect(self._on_interval_changed)

    # ── data loading ────────────────────────────────────────────
    def _load_data(self):
        self._set_status("Fetching historical data…")
        self.btn_refresh.setEnabled(False)

        sym   = self.sym_cb.currentText()
        intv  = self.intv_cb.currentText()

        if self._api_worker and self._api_worker.isRunning():
            self._api_worker.quit()

        self._api_worker = HistoricalDataWorker(sym, intv)
        self._api_worker.data_ready.connect(self._on_historical)
        self._api_worker.error.connect(self._on_api_error)
        self._api_worker.start()

    @Slot(list)
    def _on_historical(self, candles):
        self.chart.set_candles(candles)
        self._update_stats(candles)
        self._set_status(
            f"Loaded {len(candles)} candles  |  "
            f"{self.sym_cb.currentText()} {self.intv_cb.currentText()}"
        )
        self.btn_refresh.setEnabled(True)

    @Slot(str)
    def _on_api_error(self, msg):
        self._set_status(f"API Error: {msg}")
        self.btn_refresh.setEnabled(True)

    # ── helpers ─────────────────────────────────────────────────
    def _update_stats(self, candles, live_close=None):
        if not candles:
            return
        close  = live_close if live_close is not None else candles[-1].close
        open24 = candles[0].open
        hi24   = max(c.high for c in candles)
        lo24   = min(c.low  for c in candles)
        vol    = sum(c.volume for c in candles)
        chg    = close - open24
        chg_p  = (chg / open24 * 100) if open24 else 0
        color  = Theme.GREEN.name() if chg >= 0 else Theme.RED.name()

        self._lbl_price.setText(f"{close:,.4f}")
        self._lbl_change.setText(f"{chg:+.4f} ({chg_p:+.2f}%)")
        self._lbl_change.setStyleSheet(f"color:{color}; font-family:Consolas; font-size:9pt; font-weight:bold;")
        self._lbl_high.setText(f"{hi24:,.4f}")
        self._lbl_low.setText(f"{lo24:,.4f}")
        self._lbl_vol.setText(f"{vol:,.0f}")

    def _set_status(self, msg: str):
        self._status.setText(f"  {msg}")

    def _on_symbol_changed(self, _):
        self._load_data()

    def _on_interval_changed(self, _):
        self._load_data()

    def closeEvent(self, event):
        super().closeEvent(event)


