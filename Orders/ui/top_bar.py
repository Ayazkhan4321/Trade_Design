"""
top_bar.py  –  Orders / History / Inbox / Logs tab bar + icon buttons.

THEME ARCHITECTURE:
  TopBar connects DIRECTLY to ThemeManager.theme_changed and receives tokens
  inline via the signal. This means _apply_styles() runs synchronously on
  every theme change with no QTimer and no processEvents() race.

  Style strategy (v2 — single-stylesheet, objectName selectors):
    All styles live in ONE self.setStyleSheet() call on the TopBar parent,
    using #objectName selectors (QTabBar#OrdersTabBar, QPushButton#OrdersSettingsBtn …).

    Why this is correct:
      • A parent widget's own stylesheet is resolved BEFORE the app stylesheet,
        so these rules always win over any matching rule in the global QSS
        applied by ThemeApplier.apply_to_app().
      • The old approach set a generic QTabBar stylesheet directly on the tabbar
        child widget, then used unpolish → clear → setStyleSheet → polish.  That
        created a brief window with NO widget-level stylesheet; if
        QApplication.processEvents() fired (as it does in ThemePopup._on_toggle)
        during that window, Qt fell back to the app stylesheet which still
        carried the previous theme's accent colour — producing the stale-colour bug.
      • A single atomic self.setStyleSheet() has no such window.

  The _on_theme_changed lambda is stored as an instance attribute to prevent
  PySide6 from garbage-collecting the connection, and is explicitly disconnected
  in closeEvent() to avoid a dangling reference crash if the widget is destroyed
  while ThemeManager is still alive.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QTabBar

try:
    from Theme.theme_manager import ThemeManager
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


class TopBar(QWidget):
    tab_changed        = Signal(str)
    settings_requested = Signal()
    funnel_requested   = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Tab bar ───────────────────────────────────────────────────────
        self.tabbar = QTabBar(self)
        self.tabbar.setObjectName("OrdersTabBar")
        self.tabbar.setDrawBase(False)
        self.tabbar.setElideMode(Qt.ElideRight)
        self.tabbar.setExpanding(False)
        self.tabbar.setTabsClosable(False)
        self.tabbar.setUsesScrollButtons(True)
        self.tabbar.setFixedHeight(28)
        self.tabbar.setContentsMargins(0, 0, 0, 0)

        self.tabbar.addTab("Order (2)")
        self.tabbar.addTab("History")
        self.tabbar.addTab("Inbox")
        self.tabbar.addTab("Logs")

        self.tabs = [self.tabbar.tabText(i) for i in range(self.tabbar.count())]

        self.tabbar.currentChanged.connect(
            lambda idx: self.tab_changed.emit(self.tabbar.tabText(idx))
        )
        layout.addWidget(self.tabbar)
        layout.addStretch()

        # ── Settings button (⚙) ──────────────────────────────────────────
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setFixedSize(26, 26)
        self.settings_btn.setObjectName("OrdersSettingsBtn")
        self.settings_btn.clicked.connect(self.settings_requested)
        layout.addWidget(self.settings_btn)

        # ── Funnel / filter button (⏷) ───────────────────────────────────
        self.funnel_btn = QPushButton("⏷")
        self.funnel_btn.setCursor(Qt.PointingHandCursor)
        self.funnel_btn.setToolTip("Filter")
        self.funnel_btn.setFixedSize(34, 26)
        self.funnel_btn.setObjectName("OrdersFunnelBtn")
        self.funnel_btn.clicked.connect(self.funnel_requested)
        layout.addWidget(self.funnel_btn)

        # ── Initial paint ─────────────────────────────────────────────────
        # Apply with current tokens immediately (no defer needed at init time,
        # no processEvents() race exists yet).
        self._apply_styles(self._get_tokens())

        try:
            self.tabbar.setCurrentIndex(0)
            # tab_changed is already emitted by the currentChanged lambda above
        except Exception:
            pass

        # ── Live theme updates ────────────────────────────────────────────
        # KEY: connect directly — no QTimer.singleShot.
        # _apply_styles() receives tokens FROM the signal, so it runs
        # synchronously and before QApplication.processEvents() in
        # theme_popup._on_toggle() gets a chance to trigger another pass.
        # Store lambda to prevent PySide6 garbage-collection.
        if _THEME_AVAILABLE:
            try:
                self._on_theme_changed = lambda name, tokens: self._apply_styles(tokens)
                ThemeManager.instance().theme_changed.connect(self._on_theme_changed)
            except Exception:
                pass

    def closeEvent(self, event):
        """Disconnect theme listener to prevent dangling reference after destruction."""
        if _THEME_AVAILABLE:
            try:
                ThemeManager.instance().theme_changed.disconnect(self._on_theme_changed)
            except Exception:
                pass
        super().closeEvent(event)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #
    def _get_tokens(self) -> dict:
        """Fetch current tokens from ThemeManager (used only for initial paint)."""
        if _THEME_AVAILABLE:
            try:
                return ThemeManager.instance().tokens()
            except Exception:
                pass
        return {}

    def _apply_styles(self, tokens: dict):
        """Apply all styles using *tokens* received directly from theme_changed.

        FIX (v2): Everything is applied in a SINGLE self.setStyleSheet() call
        using objectName selectors (#OrdersTabBar, #OrdersSettingsBtn, etc.).

        Why this beats the old approach:
          • A parent widget's own stylesheet is resolved BEFORE the app
            stylesheet, regardless of selector specificity.  The old code set
            a generic QTabBar stylesheet directly on the tabbar widget, which
            Qt could lose during the global app.setStyleSheet() re-polish that
            the main window triggers after every theme_changed signal.
          • The unpolish → clear → setStyleSheet → polish dance introduced a
            brief window where the tabbar had NO widget-level stylesheet; if
            QApplication.processEvents() (called from ThemePopup._on_toggle)
            fired during that window, Qt fell back to the app stylesheet which
            still carried the PREVIOUS theme's accent colour.
          • A single atomic self.setStyleSheet() call eliminates both races:
            there is no cleared-then-reset window, and the objectName selectors
            are specific enough to beat any conflicting rule in the app QSS.
        """
        t = tokens if tokens else {}

        bg_inactive   = t.get("bg_tab_inactive",  "transparent")
        bg_active     = t.get("bg_tab_active",    "#e6f0ff")
        bg_hover      = t.get("bg_button_hover",  "#e2e8f0")
        text_active   = t.get("text_tab_active",  "#1976d2")
        text_inactive = t.get("text_tab_inactive","#6b7280")
        accent        = t.get("accent",           "#1976d2")
        text_primary  = t.get("text_primary",     "#1a202c")
        bg_panel      = t.get("bg_panel",         "transparent")

        # ── Single atomic stylesheet on the TopBar parent ─────────────────
        # Using objectName selectors guarantees these rules win over any
        # matching rule in the application-level stylesheet set elsewhere.
        self.setStyleSheet(f"""
            TopBar {{
                background: {bg_panel};
            }}

            QTabBar#OrdersTabBar {{
                background: transparent;
                margin-top: -8px;
                margin-bottom: -6px;
            }}
            QTabBar#OrdersTabBar::tab {{
                background: {bg_inactive};
                color: {text_inactive};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 4px 12px;
                min-height: 28px;
                margin-right: -1px;
            }}
            QTabBar#OrdersTabBar::tab:selected {{
                background: {bg_active};
                color: {text_active};
                font-weight: 600;
                border-bottom: 3px solid {accent};
                margin-bottom: -6px;
            }}
            QTabBar#OrdersTabBar::tab:hover {{
                background: {bg_hover};
                color: {text_primary};
            }}
            QTabBar#OrdersTabBar::tab:last {{
                margin-right: 0;
            }}

            QPushButton#OrdersSettingsBtn,
            QPushButton#OrdersFunnelBtn {{
                background: transparent;
                border: none;
                color: {text_primary};
                font-size: 16px;
                padding: 0px;
            }}
            QPushButton#OrdersSettingsBtn:hover,
            QPushButton#OrdersFunnelBtn:hover {{
                background: {bg_hover};
                color: {accent};
                border-radius: 4px;
            }}
            QPushButton#OrdersSettingsBtn:pressed,
            QPushButton#OrdersFunnelBtn:pressed {{
                background: {bg_active};
                color: {accent};
                border-radius: 4px;
            }}
        """)

        # Clear any stale widget-level stylesheets on the children so the
        # parent's rules above are not shadowed by an old direct assignment.
        self.tabbar.setStyleSheet("")
        for btn in (self.settings_btn, self.funnel_btn):
            btn.setStyleSheet("")

        self.update()

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #
    def apply_theme(self):
        """Public re-theme entry point (e.g. called externally without tokens)."""
        self._apply_styles(self._get_tokens())

    def set_active_tab(self, name_or_index):
        """Set active tab by index or by visible tab text."""
        try:
            if isinstance(name_or_index, int):
                idx = name_or_index
            elif isinstance(name_or_index, str):
                texts = [self.tabbar.tabText(i) for i in range(self.tabbar.count())]
                if name_or_index in texts:
                    idx = texts.index(name_or_index)
                else:
                    base = name_or_index.split("(")[0].strip()
                    idx = next(
                        (i for i, txt in enumerate(texts)
                         if txt.split("(")[0].strip() == base),
                        0,
                    )
            else:
                return
            self.tabbar.setCurrentIndex(idx)
        except Exception:
            pass

    def update_buttons(self, tab_name: str):
        """Show / hide action buttons depending on which tab is active."""
        base = tab_name.split("(")[0].strip()
        self.settings_btn.setVisible(base in ("Order", "History"))
        self.funnel_btn.setVisible(base in ("History", "Logs"))