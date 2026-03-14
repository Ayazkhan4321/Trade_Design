"""
tradingview_plugin.py
=====================
Embeds the live web trading chart at http://89.116.20.215:3009/
directly inside the PySide6 app using QWebEngineView.

Replaces the custom QPainter candlestick widget entirely.
Drop-in compatible — same class name TradingChartPlugin,
same  load_symbol(symbol)  public API.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QFont, QDesktopServices

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    _WEB_OK = True
except ImportError:
    _WEB_OK = False
    print(
        "[TradingChartPlugin] PySide6-WebEngine not installed.\n"
        "  Run:  pip install PySide6-WebEngine"
    )


CHART_URL = "http://89.116.20.215:3009/"


class TradingChartPlugin(QWidget):
    """
    Embeds the web trading terminal at CHART_URL inside the PySide6 app.

    Public API (drop-in replacement for the old QPainter plugin):
        load_symbol(symbol: str)
            Notifies the embedded web page of the selected symbol via JS.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._current_symbol = ""
        self._page_ready     = False
        self._build_ui()

    # ─────────────────────────── UI BUILD ────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        if not _WEB_OK:
            self._build_fallback(root)
            return

        # ── Thin toolbar (matches app dark theme) ────────────────────
        bar = QFrame()
        bar.setFixedHeight(36)
        bar.setStyleSheet(
            "background: #1e222d;"
            "border-bottom: 1px solid #2a2e39;"
        )
        hbox = QHBoxLayout(bar)
        hbox.setContentsMargins(10, 0, 10, 0)
        hbox.setSpacing(8)

        icon = QLabel("📊")
        icon.setFont(QFont("Segoe UI Emoji", 12))
        icon.setStyleSheet("background:transparent;")
        hbox.addWidget(icon)

        self._title = QLabel("Trading Chart")
        self._title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._title.setStyleSheet("color: #2196f3; background: transparent;")
        hbox.addWidget(self._title)

        hbox.addStretch()

        _btn_style = """
            QPushButton {
                background: #2a2e39;
                color: #d1d4dc;
                border: 1px solid #363a4a;
                border-radius: 3px;
                font-size: 14px;
                min-width: 28px;
                min-height: 24px;
            }
            QPushButton:hover { background: #2196f3; color: #fff; border-color:#2196f3; }
            QPushButton:pressed { background: #1565c0; }
        """

        btn_reload = QPushButton("⟳")
        btn_reload.setToolTip("Reload chart")
        btn_reload.setStyleSheet(_btn_style)
        btn_reload.setFixedSize(28, 24)
        btn_reload.clicked.connect(self._reload)
        hbox.addWidget(btn_reload)

        btn_ext = QPushButton("⤢")
        btn_ext.setToolTip("Open in browser")
        btn_ext.setStyleSheet(_btn_style)
        btn_ext.setFixedSize(28, 24)
        btn_ext.clicked.connect(self._open_external)
        hbox.addWidget(btn_ext)

        root.addWidget(bar)

        # ── WebEngine view ────────────────────────────────────────────
        self._view = QWebEngineView()
        self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._view.setStyleSheet("background:#131722;")

        # Settings — enable everything the trading app needs
        s = self._view.settings()
        s.setAttribute(QWebEngineSettings.JavascriptEnabled,               True)
        s.setAttribute(QWebEngineSettings.LocalStorageEnabled,             True)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.AllowRunningInsecureContent,     True)
        s.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled,           True)
        s.setAttribute(QWebEngineSettings.PluginsEnabled,                  True)
        try:
            s.setAttribute(QWebEngineSettings.WebSocketsEnabled,           True)
        except Exception:
            pass  # older Qt versions don't have this attribute

        # Load signals
        self._view.loadStarted.connect(self._on_load_started)
        self._view.loadProgress.connect(self._on_load_progress)
        self._view.loadFinished.connect(self._on_load_finished)

        root.addWidget(self._view, stretch=1)

        # ── Status bar ────────────────────────────────────────────────
        self._status = QLabel("  Connecting to chart server…")
        self._status.setFixedHeight(20)
        self._status.setFont(QFont("Segoe UI", 7))
        self._status.setStyleSheet(
            "color: #4c505e;"
            "background: #131722;"
            "border-top: 1px solid #2a2e39;"
            "padding-left: 8px;"
        )
        root.addWidget(self._status)

        # Load the chart
        self._view.load(QUrl(CHART_URL))

    def _build_fallback(self, root):
        """Shown when QtWebEngine is not installed."""
        msg = (
            "⚠️  PySide6-WebEngine is required to display the embedded chart.\n\n"
            "Install it with:\n\n"
            "    pip install PySide6-WebEngine\n\n"
            f"Then restart the app.\n\nChart URL:  {CHART_URL}"
        )
        lbl = QLabel(msg)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFont(QFont("Segoe UI", 11))
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            "color: #787b86; background: #131722; padding: 40px;"
        )
        root.addWidget(lbl)

    # ─────────────────────────── LOAD SIGNALS ────────────────────────
    def _on_load_started(self):
        self._page_ready = False
        self._status.setText("  Loading chart…")

    def _on_load_progress(self, pct: int):
        self._status.setText(f"  Loading… {pct}%")

    def _on_load_finished(self, ok: bool):
        self._page_ready = ok
        if ok:
            self._status.setText(f"  ✓  {CHART_URL}")
            # Push any symbol that was requested before the page was ready
            if self._current_symbol:
                QTimer.singleShot(600, lambda: self._inject_symbol(self._current_symbol))
        else:
            self._status.setText(
                f"  ✗  Could not connect to chart server at {CHART_URL}"
            )

    # ─────────────────────────── ACTIONS ─────────────────────────────
    def _reload(self):
        if hasattr(self, '_view'):
            self._page_ready = False
            self._view.reload()

    def _open_external(self):
        url = CHART_URL
        if self._current_symbol:
            url = f"{CHART_URL}?symbol={self._current_symbol}"
        QDesktopServices.openUrl(QUrl(url))

    # ─────────────────────────── PUBLIC API ──────────────────────────
    def load_symbol(self, symbol: str):
        """
        Called when user clicks a row in the left-panel symbol table.

        Passes the symbol to the embedded web app via JavaScript.
        Three strategies are tried in order — whichever the web app supports:
          1. window.postMessage
          2. window.setSymbol() / window.chart.setSymbol()
          3. URL reload with ?symbol=SYM  (fallback)
        """
        sym = symbol.strip().upper()
        if not sym:
            return

        self._current_symbol = sym

        # Update toolbar title immediately
        if hasattr(self, '_title'):
            self._title.setText(f"Trading Chart  ·  {sym}")

        if not _WEB_OK or not hasattr(self, '_view'):
            return

        if self._page_ready:
            self._inject_symbol(sym)
        else:
            # Page still loading — will be applied in _on_load_finished
            pass

    def _inject_symbol(self, sym: str):
        """
        Push the symbol into the running web page without a full reload.

        Edit this JS to match whatever API your web app exposes.
        Common patterns are all tried below.
        """
        js = f"""
        (function() {{
            var sym = '{sym}';

            // 1. postMessage — web app must add:  window.addEventListener('message', ...)
            try {{ window.postMessage({{ type: 'SET_SYMBOL', symbol: sym }}, '*'); }} catch(e) {{}}

            // 2. Direct function the app might expose on window
            try {{ if (typeof window.setSymbol === 'function') window.setSymbol(sym); }} catch(e) {{}}

            // 3. Chart object API
            try {{ if (window.chart && typeof window.chart.setSymbol === 'function') window.chart.setSymbol(sym); }} catch(e) {{}}

            // 4. TradingView widget API (if app uses TradingView library)
            try {{
                if (window.tvWidget && window.tvWidget.activeChart)
                    window.tvWidget.activeChart().setSymbol(sym, function(){{}});
            }} catch(e) {{}}

            // 5. React / Redux store dispatch
            try {{
                if (window.__store__ && typeof window.__store__.dispatch === 'function')
                    window.__store__.dispatch({{ type: 'SET_SYMBOL', payload: sym }});
            }} catch(e) {{}}

        }})();
        """
        self._view.page().runJavaScript(js)

    def closeEvent(self, event):
        if _WEB_OK and hasattr(self, '_view'):
            try:
                self._view.stop()
            except Exception:
                pass
        super().closeEvent(event)