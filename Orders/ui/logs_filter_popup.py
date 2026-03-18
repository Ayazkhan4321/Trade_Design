"""
logs_filter_popup.py
====================
LogFilterPopup     – "Filter Logs"    (single From Date, 7-day window)
HistoryFilterPopup – "Custom Filter"  (All History | Custom Period with date range)

Theme strategy — DIRECT per-widget setStyleSheet() on every single widget.
No ancestor selectors. No cascading. Every widget owns its own style.
This is the only approach that reliably beats the global app stylesheet.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QDateEdit, QComboBox,
    QApplication, QSizePolicy,
)

_OUTER_PAD = 8


# ── Token resolution (same proven pattern as BulkCloseDialog) ────────────────
def _detect_dark() -> bool:
    try:
        from Theme.theme_manager import ThemeManager
        tok = ThemeManager.instance().tokens()
        val = tok.get("is_dark", None)
        if val is not None:
            if isinstance(val, bool): return val
            s = str(val).lower()
            if s in ("true", "1", "yes", "dark"): return True
            if s in ("false", "0", "no", "light"): return False
        for key in ("bg_panel", "background", "bg_primary", "bg_base", "bg"):
            cs = tok.get(key)
            if cs:
                c = QColor(cs)
                if c.isValid(): return c.lightness() < 128
    except Exception: pass
    try:
        app = QApplication.instance()
        if app: return app.palette().window().color().lightness() < 128
    except Exception: pass
    return False


def _tok() -> dict:
    try:
        from Theme.theme_manager import ThemeManager
        raw = ThemeManager.instance().tokens()
    except Exception:
        raw = {}
    dark = _detect_dark()
    def t(*keys, fd, fl):
        for k in keys:
            v = raw.get(k)
            if v: return v
        return fd if dark else fl
    return {
        "bg":       t("bg_panel","background","bg_primary",          fd="#151e2d", fl="#ffffff"),
        "bg_input": t("bg_input","bg_secondary","bg_surface",         fd="#1e2a3a", fl="#f9fafb"),
        "bg_alt":   t("bg_row_alt","bg_input","bg_secondary",         fd="#1a2535", fl="#f3f4f6"),
        "bg_hover": t("bg_hover","bg_button_hover","bg_row_hover",    fd="#1e2d3d", fl="#e2e8f0"),
        "text":     t("text_primary","text","fg",                     fd="#e2e8f0", fl="#111827"),
        "text_sec": t("text_secondary","text_muted",                  fd="#94a3b8", fl="#6b7280"),
        "border":   t("border","border_color","border_separator",     fd="#2d3a4a", fl="#e2e8f0"),
        "accent":   t("accent","primary","color_accent",              fd="#3b82f6", fl="#2563eb"),
        "sel_bg":   t("bg_tab_active","bg_selected","selection_bg",   fd="#1a3a5c", fl="#dbeafe"),
    }


def _dk(hex_color: str, amount: int = 20) -> str:
    try:
        c = QColor(hex_color)
        h, s, v, a = c.getHsv()
        c.setHsv(h, s, max(0, v - amount), a)
        return c.name()
    except Exception:
        return hex_color


# ── Direct-style helpers — called on individual widgets ───────────────────────
def _s_card(card: QFrame, bg: str, border: str):
    card.setStyleSheet(
        f"QFrame {{ background-color: {bg}; border: 1px solid {border}; border-radius: 6px; }}"
    )

def _s_label(w: QLabel, text: str, size: int = 13, bold: bool = False, italic: bool = False):
    f_weight = "700" if bold else "400"
    f_style  = "italic" if italic else "normal"
    w.setStyleSheet(
        f"QLabel {{ color: {text}; font-size: {size}px; font-weight: {f_weight}; "
        f"font-style: {f_style}; background: transparent; border: none; }}"
    )

def _s_div(w: QFrame, color: str):
    w.setStyleSheet(
        f"QFrame {{ background-color: {color}; border: none; "
        f"min-height: 1px; max-height: 1px; }}"
    )

def _s_close(btn: QPushButton, text_sec: str, bg_hover: str, text: str):
    btn.setStyleSheet(
        f"QPushButton {{ background: transparent; color: {text_sec}; border: none; "
        f"font-size: 13px; font-weight: 600; border-radius: 4px; padding: 0; }}"
        f"QPushButton:hover {{ background-color: rgba(239,68,68,0.15); color: #ef4444; }}"
        f"QPushButton:pressed {{ background-color: rgba(239,68,68,0.30); color: #ef4444; }}"
    )

def _s_date(w: QDateEdit, bg: str, text: str, border: str, accent: str, sel: str):
    w.setStyleSheet(
        f"QDateEdit {{ background-color: {bg}; color: {text}; "
        f"border: 1px solid {border}; border-radius: 4px; padding: 2px 6px; font-size: 13px; }}"
        f"QDateEdit:focus {{ border: 1px solid {accent}; }}"
        f"QDateEdit::drop-down {{ border: none; width: 18px; }}"
        f"QDateEdit QAbstractItemView {{ background-color: {bg}; color: {text}; "
        f"selection-background-color: {sel}; border: 1px solid {border}; }}"
    )

def _s_combo(w: QComboBox, bg: str, text: str, border: str, accent: str, sel: str):
    w.setStyleSheet(
        f"QComboBox {{ background-color: {bg}; color: {text}; "
        f"border: 1px solid {border}; border-radius: 4px; padding: 2px 6px; font-size: 13px; }}"
        f"QComboBox:focus {{ border: 1px solid {accent}; }}"
        f"QComboBox::drop-down {{ border: none; width: 18px; }}"
        f"QComboBox QAbstractItemView {{ background-color: {bg}; color: {text}; "
        f"selection-background-color: {sel}; border: 1px solid {border}; }}"
    )

def _s_ghost(btn: QPushButton, text: str, border: str, bg_hover: str):
    btn.setStyleSheet(
        f"QPushButton {{ background: transparent; color: {text}; "
        f"border: 1px solid {border}; border-radius: 4px; "
        f"font-size: 12px; font-weight: 600; padding: 0 10px; }}"
        f"QPushButton:hover {{ background-color: {bg_hover}; }}"
    )

def _s_primary(btn: QPushButton, accent: str):
    btn.setStyleSheet(
        f"QPushButton {{ background-color: {accent}; color: #ffffff; border: none; "
        f"border-radius: 4px; font-size: 12px; font-weight: 700; padding: 0 14px; }}"
        f"QPushButton:hover {{ background-color: {_dk(accent)}; }}"
        f"QPushButton:pressed {{ background-color: {_dk(accent, 35)}; }}"
    )

def _s_mode_row(row: QWidget, mode: str, selected: bool,
                bg: str, bg_hover: str, accent: str, text: str):
    border_l = f"border-left: 3px solid {accent};" if selected else "border-left: 3px solid transparent;"
    bg_row   = bg_hover if selected else bg
    row.setStyleSheet(
        f"QWidget#fp_mode_row_{mode} {{ background-color: {bg_row}; {border_l} border-radius: 0px; }}"
        f"QWidget#fp_mode_row_{mode}:hover {{ background-color: {bg_hover}; }}"
    )
    row._text_lbl.setStyleSheet(
        f"QLabel {{ color: {''+accent+'' if selected else text}; font-size: 13px; "
        f"font-weight: {'700' if selected else '400'}; background: transparent; border: none; }}"
    )
    row._icon_lbl.setStyleSheet(
        "QLabel { background: transparent; border: none; font-size: 15px; }"
    )

def _s_panel_bg(panel: QWidget, bg: str, border: str):
    panel.setStyleSheet(
        f"QWidget#fp_custom_panel {{ background-color: {bg}; "
        f"border-top: 1px solid {border}; border-bottom: 1px solid {border}; }}"
    )


# ── Base ──────────────────────────────────────────────────────────────────────
class _BaseFilterPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(_OUTER_PAD, _OUTER_PAD, _OUTER_PAD, _OUTER_PAD)
        outer.setSpacing(0)

        self._card = QFrame(self)
        self._card.setObjectName("fp_card")
        self._card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._card.setAttribute(Qt.WA_StyledBackground, True)
        outer.addWidget(self._card)

        self._card_layout = QVBoxLayout(self._card)
        self._card_layout.setContentsMargins(16, 12, 16, 14)
        self._card_layout.setSpacing(10)

        # Keep outer shell fully transparent — card carries all visible styling
        self.setStyleSheet("QWidget { background: transparent; border: none; }")

        try:
            from Theme.theme_manager import ThemeManager
            self._on_theme_cb = lambda n, tt: self._apply_theme()
            ThemeManager.instance().theme_changed.connect(self._on_theme_cb)
        except Exception:
            pass

    def show_near(self, anchor: QWidget):
        # Always re-apply theme when opening — catches changes made while popup was hidden
        self._apply_theme()
        self.adjustSize(); self.ensurePolished()
        pw = self.width(); ph = max(self.sizeHint().height(), self.height())
        screen = QApplication.screenAt(anchor.mapToGlobal(QPoint(0, 0))) or QApplication.primaryScreen()
        avail  = screen.availableGeometry()
        btn_tl = anchor.mapToGlobal(QPoint(0, 0))
        btn_tr = anchor.mapToGlobal(QPoint(anchor.width(), 0))
        btn_br = anchor.mapToGlobal(QPoint(anchor.width(), anchor.height()))
        x      = btn_br.x() - pw + _OUTER_PAD
        y_below = btn_br.y() + 4;  y_above = btn_tr.y() - ph - 4
        scr_mid = avail.top() + avail.height() // 2
        if btn_tl.y() >= scr_mid:
            y = y_above if y_above >= avail.top() else avail.top() + 4
        else:
            y = y_below if y_below + ph <= avail.bottom() else (y_above if y_above >= avail.top() else avail.bottom() - ph - 4)
        x = max(avail.left() + 4, min(x, avail.right() - pw - 4))
        y = max(avail.top()  + 4, min(y, avail.bottom() - ph - 4))
        self.move(x, y); self.show(); self.raise_(); self.activateWindow()

    def _apply_theme(self): raise NotImplementedError

    def _make_divider(self) -> QFrame:
        d = QFrame(); d.setObjectName("fp_div")
        d.setFrameShape(QFrame.HLine); d.setFixedHeight(1)
        return d

    def closeEvent(self, event):
        try:
            from Theme.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.disconnect(self._on_theme_cb)
        except Exception: pass
        super().closeEvent(event)


# ── Logs filter ───────────────────────────────────────────────────────────────
class LogFilterPopup(_BaseFilterPopup):
    filters_applied = Signal(dict)
    filters_cleared = Signal()
    _MAX_DAYS = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(330)
        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        cl = self._card_layout

        # Title
        row = QHBoxLayout(); row.setContentsMargins(0,0,0,0); row.setSpacing(0)
        self._lbl_title = QLabel("Filter Logs")
        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedSize(22, 22); self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.hide)
        row.addWidget(self._lbl_title); row.addStretch(); row.addWidget(self._btn_close)
        cl.addLayout(row)

        self._div_top = self._make_divider(); cl.addWidget(self._div_top)

        self._lbl_from = QLabel("From Date (last 7 days up to today)")
        cl.addWidget(self._lbl_from)

        today = QDate.currentDate()
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("dd-MMM-yyyy")
        self._date_edit.setDate(today.addDays(-self._MAX_DAYS + 1))
        self._date_edit.setMinimumDate(today.addDays(-self._MAX_DAYS + 1))
        self._date_edit.setMaximumDate(today)
        self._date_edit.setFixedHeight(32)
        cl.addWidget(self._date_edit)

        self._lbl_hint = QLabel("Results will be limited to the 7-day window ending today.")
        self._lbl_hint.setWordWrap(True)
        cl.addWidget(self._lbl_hint)

        cl.addSpacing(4)
        self._div_bot = self._make_divider(); cl.addWidget(self._div_bot)
        cl.addSpacing(4)

        # Buttons
        self._btn_clear  = QPushButton("Clear All");     self._btn_clear.setFixedHeight(30);  self._btn_clear.setCursor(Qt.PointingHandCursor)
        self._btn_cancel = QPushButton("Cancel");        self._btn_cancel.setFixedHeight(30); self._btn_cancel.setCursor(Qt.PointingHandCursor)
        self._btn_apply  = QPushButton("Apply Filters"); self._btn_apply.setFixedHeight(30);  self._btn_apply.setCursor(Qt.PointingHandCursor)
        self._btn_clear.clicked.connect(self._on_clear)
        self._btn_cancel.clicked.connect(self.hide)
        self._btn_apply.clicked.connect(self._on_apply)
        br = QHBoxLayout(); br.setContentsMargins(0,0,0,0); br.setSpacing(8)
        br.addWidget(self._btn_clear); br.addStretch(); br.addWidget(self._btn_cancel); br.addWidget(self._btn_apply)
        cl.addLayout(br)

    def _apply_theme(self):
        c = _tok()
        _s_card(self._card, c["bg"], c["border"])
        _s_label(self._lbl_title, c["text"], 14, bold=True)
        _s_close(self._btn_close, c["text_sec"], c["bg_hover"], c["text"])
        _s_div(self._div_top, c["border"])
        _s_label(self._lbl_from,  c["text"], 12, bold=True)
        _s_date(self._date_edit, c["bg_input"], c["text"], c["border"], c["accent"], c["sel_bg"])
        _s_label(self._lbl_hint,  c["text_sec"], 11)
        _s_div(self._div_bot, c["border"])
        _s_ghost(self._btn_clear,  c["text_sec"], c["border"], c["bg_hover"])
        _s_ghost(self._btn_cancel, c["text"],     c["border"], c["bg_hover"])
        _s_primary(self._btn_apply, c["accent"])

    def _on_apply(self):
        self.filters_applied.emit({"from_date": self._date_edit.date(), "to_date": QDate.currentDate()})
        self.hide()

    def _on_clear(self):
        self._date_edit.setDate(QDate.currentDate().addDays(-self._MAX_DAYS + 1))
        self.filters_cleared.emit(); self.hide()


# ── History / Custom filter ───────────────────────────────────────────────────
class HistoryFilterPopup(_BaseFilterPopup):
    """
    Two-mode filter:
      All History   — fetch everything, no date range
      Custom Period — Period preset + manual From / To dates
    """
    filters_applied = Signal(dict)
    filters_cleared = Signal()

    _PERIODS = ["Select Period", "Today", "Yesterday", "Last 7 Days",
                "Last 30 Days", "This Month", "Last Month"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(360)
        self._mode = "all"
        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        cl = self._card_layout
        cl.setSpacing(0)

        # ── Title ─────────────────────────────────────────────────────────
        title_row = QHBoxLayout(); title_row.setContentsMargins(0, 0, 0, 8); title_row.setSpacing(0)
        self._lbl_title = QLabel("Custom Filter")
        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedSize(22, 22); self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.clicked.connect(self.hide)
        title_row.addWidget(self._lbl_title); title_row.addStretch(); title_row.addWidget(self._btn_close)
        cl.addLayout(title_row)

        # ── All History row ───────────────────────────────────────────────
        self._row_all = self._make_mode_row("🕐", "All History", "all")
        cl.addWidget(self._row_all)

        self._div_mid = self._make_divider(); cl.addWidget(self._div_mid)

        # ── Custom Period row ─────────────────────────────────────────────
        self._row_custom = self._make_mode_row("📅", "Custom Period", "custom")
        cl.addWidget(self._row_custom)

        # ── Custom period expansion panel ─────────────────────────────────
        self._custom_panel = QWidget()
        self._custom_panel.setObjectName("fp_custom_panel")
        self._custom_panel.setAttribute(Qt.WA_StyledBackground, True)
        panel_lay = QVBoxLayout(self._custom_panel)
        panel_lay.setContentsMargins(16, 12, 16, 12)
        panel_lay.setSpacing(10)

        # Period combo
        period_row = QHBoxLayout(); period_row.setContentsMargins(0,0,0,0); period_row.setSpacing(8)
        self._lbl_period = QLabel("Period:"); self._lbl_period.setFixedWidth(52)
        self._period_combo = QComboBox()
        self._period_combo.addItems(self._PERIODS)
        self._period_combo.setFixedHeight(30)
        self._period_combo.currentIndexChanged.connect(self._on_period_changed)
        period_row.addWidget(self._lbl_period); period_row.addWidget(self._period_combo, 1)
        panel_lay.addLayout(period_row)

        # From date (full width)
        today = QDate.currentDate()
        from_row = QHBoxLayout(); from_row.setContentsMargins(0,0,0,0); from_row.setSpacing(8)
        self._lbl_from = QLabel("From:"); self._lbl_from.setFixedWidth(52)
        self._from_edit = QDateEdit()
        self._from_edit.setCalendarPopup(True); self._from_edit.setDisplayFormat("dd-MM-yyyy")
        self._from_edit.setDate(today.addDays(-30)); self._from_edit.setMaximumDate(today)
        self._from_edit.setFixedHeight(30); self._from_edit.setMinimumWidth(120)
        from_row.addWidget(self._lbl_from); from_row.addWidget(self._from_edit, 1)
        panel_lay.addLayout(from_row)

        # To date (full width)
        to_row = QHBoxLayout(); to_row.setContentsMargins(0,0,0,0); to_row.setSpacing(8)
        self._lbl_to = QLabel("To:"); self._lbl_to.setFixedWidth(52)
        self._to_edit = QDateEdit()
        self._to_edit.setCalendarPopup(True); self._to_edit.setDisplayFormat("dd-MM-yyyy")
        self._to_edit.setDate(today); self._to_edit.setMaximumDate(today)
        self._to_edit.setFixedHeight(30); self._to_edit.setMinimumWidth(120)
        to_row.addWidget(self._lbl_to); to_row.addWidget(self._to_edit, 1)
        panel_lay.addLayout(to_row)

        # Ok / Cancel inside panel
        ok_row = QHBoxLayout(); ok_row.setContentsMargins(0, 4, 0, 0); ok_row.setSpacing(8)
        ok_row.addStretch()
        self._btn_cancel2 = QPushButton("Cancel"); self._btn_cancel2.setFixedHeight(30); self._btn_cancel2.setCursor(Qt.PointingHandCursor)
        self._btn_ok      = QPushButton("Ok");     self._btn_ok.setFixedHeight(30);     self._btn_ok.setCursor(Qt.PointingHandCursor)
        self._btn_cancel2.clicked.connect(lambda: self._set_mode("all"))
        self._btn_ok.clicked.connect(self._on_apply_custom)
        ok_row.addWidget(self._btn_cancel2); ok_row.addWidget(self._btn_ok)
        panel_lay.addLayout(ok_row)

        cl.addWidget(self._custom_panel)
        self._custom_panel.setVisible(False)

        # ── Bottom divider + all-history buttons ──────────────────────────
        self._div_bot = self._make_divider(); cl.addWidget(self._div_bot)

        bot_row = QHBoxLayout(); bot_row.setContentsMargins(0, 8, 0, 0); bot_row.setSpacing(8)
        self._btn_clear_all = QPushButton("Clear All");     self._btn_clear_all.setFixedHeight(30); self._btn_clear_all.setCursor(Qt.PointingHandCursor)
        self._btn_apply_all = QPushButton("Apply Filters"); self._btn_apply_all.setFixedHeight(30); self._btn_apply_all.setCursor(Qt.PointingHandCursor)
        self._btn_clear_all.clicked.connect(self._on_clear)
        self._btn_apply_all.clicked.connect(self._on_apply_all)
        bot_row.addWidget(self._btn_clear_all); bot_row.addStretch(); bot_row.addWidget(self._btn_apply_all)
        cl.addLayout(bot_row)

        self._set_mode("all")

    def _make_mode_row(self, icon: str, label: str, mode: str) -> QWidget:
        row = QWidget(); row.setObjectName(f"fp_mode_row_{mode}")
        row.setAttribute(Qt.WA_StyledBackground, True)
        row.setCursor(Qt.PointingHandCursor); row.setFixedHeight(46)
        lay = QHBoxLayout(row); lay.setContentsMargins(12, 0, 12, 0); lay.setSpacing(10)
        icon_lbl = QLabel(icon); icon_lbl.setFixedWidth(22); icon_lbl.setAlignment(Qt.AlignCenter)
        text_lbl = QLabel(label)
        lay.addWidget(icon_lbl); lay.addWidget(text_lbl); lay.addStretch()
        row._icon_lbl = icon_lbl; row._text_lbl = text_lbl; row._mode = mode
        row.mousePressEvent = lambda e, m=mode: self._set_mode(m)
        return row

    def _set_mode(self, mode: str):
        self._mode = mode
        is_custom = (mode == "custom")
        self._row_all.setVisible(not is_custom)
        self._div_mid.setVisible(not is_custom)
        self._custom_panel.setVisible(is_custom)
        self._div_bot.setVisible(not is_custom)
        self._btn_clear_all.setVisible(not is_custom)
        self._btn_apply_all.setVisible(not is_custom)
        # Force Qt to recalculate layout and resize the popup window
        self._card.updateGeometry()
        self._card.adjustSize()
        self.updateGeometry()
        self.resize(self.sizeHint())
        self.adjustSize()
        self._restyle_mode_rows()

    def _on_period_changed(self, idx: int):
        today = QDate.currentDate()
        preset = self._PERIODS[idx]
        m = {
            "Today":        (today, today),
            "Yesterday":    (today.addDays(-1), today.addDays(-1)),
            "Last 7 Days":  (today.addDays(-6), today),
            "Last 30 Days": (today.addDays(-29), today),
            "This Month":   (QDate(today.year(), today.month(), 1), today),
            "Last Month":   (QDate(today.year(), today.month(), 1).addMonths(-1),
                             QDate(today.year(), today.month(), 1).addDays(-1)),
        }
        if preset in m:
            self._from_edit.setDate(m[preset][0]); self._to_edit.setDate(m[preset][1])

    def _on_apply_all(self):
        self.filters_applied.emit({"mode": "all", "period": "All History",
                                   "from_date": None, "to_date": None})
        self.hide()

    def _on_apply_custom(self):
        self.filters_applied.emit({
            "mode": "custom", "period": self._period_combo.currentText(),
            "from_date": self._from_edit.date(), "to_date": self._to_edit.date(),
        })
        self.hide()

    def show_near(self, anchor):
        """Always open in All History mode — reset any previous Custom Period state."""
        self._set_mode("all")
        super().show_near(anchor)

    def _on_clear(self):
        self._set_mode("all"); self._period_combo.setCurrentIndex(0)
        today = QDate.currentDate()
        self._from_edit.setDate(today.addDays(-30)); self._to_edit.setDate(today)
        self.filters_cleared.emit(); self.hide()

    # ── Theme — every widget styled directly ─────────────────────────────────
    def _apply_theme(self):
        c = _tok()
        bg       = c["bg"];      bg_input = c["bg_input"]; bg_alt  = c["bg_alt"]
        bg_hover = c["bg_hover"]; text    = c["text"];     text_sec = c["text_sec"]
        border   = c["border"];   accent  = c["accent"];   sel_bg  = c["sel_bg"]

        # Card
        _s_card(self._card, bg, border)
        # Outer shell transparent
        self.setStyleSheet("HistoryFilterPopup { background: transparent; border: none; }")

        # Title + close
        _s_label(self._lbl_title, text, 14, bold=True)
        _s_close(self._btn_close, text_sec, bg_hover, text)

        # Mode rows (All History + Custom Period)
        self._restyle_mode_rows()

        # Dividers
        _s_div(self._div_mid, border)
        _s_div(self._div_bot, border)

        # Custom panel background
        _s_panel_bg(self._custom_panel, bg_alt, border)

        # All widgets inside custom panel — styled directly
        _s_label(self._lbl_period, text, 12, bold=True)
        _s_combo(self._period_combo, bg_input, text, border, accent, sel_bg)
        _s_label(self._lbl_from, text, 12, bold=True)
        _s_date(self._from_edit, bg_input, text, border, accent, sel_bg)
        _s_label(self._lbl_to, text, 12, bold=True)
        _s_date(self._to_edit,   bg_input, text, border, accent, sel_bg)
        _s_ghost(self._btn_cancel2, text, border, bg_hover)
        _s_primary(self._btn_ok, accent)

        # Bottom bar buttons
        _s_ghost(self._btn_clear_all, text_sec, border, bg_hover)
        _s_primary(self._btn_apply_all, accent)

    def _restyle_mode_rows(self):
        c = _tok()
        for row, mode in [(self._row_all, "all"), (self._row_custom, "custom")]:
            _s_mode_row(row, mode, self._mode == mode,
                        c["bg"], c["bg_hover"], c["accent"], c["text"])