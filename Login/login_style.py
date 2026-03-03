"""login_style.py – Theme-aware styling for the Login dialog.

All colours are sourced from ThemeManager tokens so the login page
automatically adapts when the user switches Dark / Light / Crazy / Time themes.

Public API (same as before, no import changes needed):
    apply_dialog_border(dialog)
    apply_login_styles(ui)
    apply_theme_to_login(dialog, ui)   ← new: call once then connect to theme_changed
"""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_tokens() -> dict:
    """Return current theme tokens (falls back to light palette if theme unavailable)."""
    try:
        from Theme.theme_manager import ThemeManager
        return ThemeManager.instance().tokens()
    except Exception:
        return {
            "bg_window":     "#ffffff",
            "bg_panel":      "#f5f5f5",
            "bg_input":      "#f5f5f5",
            "text_primary":  "#1a202c",
            "text_secondary":"#4a5568",
            "text_muted":    "#9ca3af",
            "accent":        "#e53935",
            "accent_hover":  "#c62828",
            "border_primary":"#e0e0e0",
            "border_focus":  "#e53935",
        }


def _is_dark(tokens: dict) -> bool:
    bg = tokens.get("bg_window", "#ffffff")
    return QColor(bg).lightness() < 128


def _accent(tokens: dict) -> str:
    """Return the current accent colour – for crazy themes this is the swatch colour."""
    # Crazy themes have a coloured accent; dark/light use blue or red depending on prefs.
    # We always use the theme's accent token which is already set correctly.
    return tokens.get("accent", "#e53935")


# ─────────────────────────────────────────────────────────────────────────────
# apply_dialog_border – called once on construction
# ─────────────────────────────────────────────────────────────────────────────
def apply_dialog_border(dialog):
    """Apply the overall dialog background (token-aware)."""
    t  = _get_tokens()
    bg = t.get("bg_window", "#ffffff")
    dialog.setStyleSheet(f"QDialog {{ background-color: {bg}; }}")


# ─────────────────────────────────────────────────────────────────────────────
# apply_login_styles – legacy entry point (calls full theme apply)
# ─────────────────────────────────────────────────────────────────────────────
def apply_login_styles(ui):
    """Apply theme-aware styles to all login widgets."""
    apply_theme_to_login(None, ui)


# ─────────────────────────────────────────────────────────────────────────────
# apply_theme_to_login – full theme apply (dialog + all widgets)
# ─────────────────────────────────────────────────────────────────────────────
def apply_theme_to_login(dialog, ui):
    """
    Token-driven login page styling.

    Call this once on __init__, then connect to ThemeManager.theme_changed:
        mgr.theme_changed.connect(lambda n, t: apply_theme_to_login(self, self.ui))
    """
    t   = _get_tokens()
    acc = _accent(t)
    dark = _is_dark(t)

    bg        = t.get("bg_popup",        "#1e2433" if dark else "#ffffff")
    bg_panel  = t.get("bg_popup",        "#1e2433" if dark else "#ffffff")
    bg_input  = t.get("bg_input",       "#1e2433" if dark else "#f5f5f5")
    txt       = t.get("text_primary",   "#e8eaf6" if dark else "#1a202c")
    txt_muted = t.get("text_muted",     "#5a6482" if dark else "#9ca3af")
    txt_sec   = t.get("text_secondary", "#9099b4" if dark else "#4a5568")
    bdr       = t.get("border_primary", "#2d3448" if dark else "#e0e0e0")
    bdr_focus = t.get("border_focus",   acc)
    acc_h     = t.get("accent_hover",   "#c62828")

    # Dialog background
    # if dialog is not None:
    #     dialog.setStyleSheet(f"QDialog {{ background-color: {bg}; }}")
    if dialog is not None:
        from PySide6.QtGui import QPalette, QColor
        pal = dialog.palette()
        pal.setColor(QPalette.Window, QColor(bg))
        dialog.setPalette(pal)
        dialog.setAutoFillBackground(True)
        dialog.setStyleSheet(f"QDialog {{ background-color: {bg}; }} QDialog QWidget {{ background-color: {bg}; }}")
    # ── Logo label — match dialog background so no white box shows ──
    try:
        ui.lb_logo.setStyleSheet(f"QLabel {{ background-color: transparent; }}")
        ui.layoutWidget.setStyleSheet(f"background-color: {bg};")
    except Exception:
        pass
    # ── Live / Demo buttons ──
    _btn_style = f"""
        QPushButton {{
            background-color: {'transparent' if dark else '#ffffff'};
            color: {acc};
            border: 2px solid {acc};
            border-radius: 18px;
            padding: 8px 25px;
            font-size: 14px;
            font-weight: bold;
            min-height: 20px;
            max-height: 30px;
        }}
        QPushButton:checked {{
            background-color: {acc};
            color: white;
        }}
        QPushButton:hover {{
            background-color: {'rgba(255,255,255,0.08)' if dark else '#FFEBEE'};
        }}
        QPushButton:checked:hover {{
            background-color: {acc_h};
            color: white;
        }}
    """
    try:
        ui.btn_live.setStyleSheet(_btn_style)
        ui.btn_demo.setStyleSheet(_btn_style)
    except Exception:
        pass

    # ── Input fields ──
    _input_style = f"""
        QLineEdit {{
            background-color: {bg_input};
            color: {txt};
            border: 1px solid {bdr};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 2px solid {bdr_focus};
            background-color: {bg_input};
        }}
        QLineEdit::placeholder {{
            color: {txt_muted};
        }}
    """
    try:
        ui.input_email.setStyleSheet(_input_style)
        ui.input_password.setStyleSheet(_input_style)
    except Exception:
        pass

    # ── Icon labels ──
    _icon_style = f"""
        QLabel {{
            background-color: transparent;
            min-width: 24px;
            max-width: 24px;
            min-height: 20px;
            max-height: 20px;
        }}
    """
    try:
        if hasattr(ui, "icon_email"):
            ui.icon_email.setStyleSheet(_icon_style)
            px = QPixmap(":/Main_Window/Icons/Login_to_trade.png")
            if not px.isNull():
                from PySide6.QtCore import Qt as Qt_
                ui.icon_email.setPixmap(px.scaled(24, 24, Qt_.KeepAspectRatio, Qt_.SmoothTransformation))
        if hasattr(ui, "icon_password"):
            ui.icon_password.setStyleSheet(_icon_style)
            px = QPixmap(":/Main_Window/Icons/password.png")
            if not px.isNull():
                from PySide6.QtCore import Qt as Qt_
                ui.icon_password.setPixmap(px.scaled(24, 24, Qt_.KeepAspectRatio, Qt_.SmoothTransformation))
    except Exception:
        pass

    # ── Sign In button ──
    try:
        ui.btn_signin.setStyleSheet(f"""
            QPushButton {{
                background-color: {acc};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 15px;
                font-weight: bold;
                min-height: 20px;
                max-height: 35px;
            }}
            QPushButton:hover  {{ background-color: {acc_h}; }}
            QPushButton:pressed {{ background-color: {t.get('accent_hover', '#c62828')}; }}
            QPushButton:disabled {{ background-color: {'#3a4460' if dark else '#BDBDBD'}; color: {txt_muted}; }}
        """)
    except Exception:
        pass

    # ── Forgot password label ──
    try:
        ui.lbl_forgot_password.setStyleSheet(f"""
            QLabel {{
                color: {acc};
                font-size: 12px;
            }}
            QLabel:hover {{
                color: {t.get('text_link', '#64b5f6' if dark else '#1976d2')};
                text-decoration: underline;
            }}
        """)
        ui.lbl_forgot_password.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass

    # ── Create account label ──
    try:
        ui.lbl_create_account.setStyleSheet(f"""
            QLabel {{
                color: {acc};
                font-size: 12px;
                font-weight: bold;
            }}
            QLabel:hover {{
                color: {t.get('text_link', '#64b5f6' if dark else '#1976d2')};
                text-decoration: underline;
            }}
        """)
        ui.lbl_create_account.setCursor(Qt.PointingHandCursor)
    except Exception:
        pass

    # ── Checkbox ──
    try:
        ui.cb_remember_me.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                color: {txt_sec};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {bdr};
                border-radius: 3px;
                background: {bg_input};
            }}
            QCheckBox::indicator:checked {{
                background-color: {acc};
                border-color: {acc};
            }}
        """)
    except Exception:
        pass

    # ── "New to trading?" label ──
    try:
        ui.lb_trading.setStyleSheet(f"QLabel {{ color: {txt_muted}; font-size: 12px; }}")
    except Exception:
        pass

    # ── Container / panel background (widget that wraps the form) ──
    # The login dialog itself is a QDialog; make sure the inner widget respects theme
    try:
        # Style any frame or central widget inside the dialog
        if dialog is not None:
            for child in dialog.findChildren(__import__('PySide6.QtWidgets', fromlist=['QFrame']).QFrame):
                child.setStyleSheet(f"background: {bg_panel}; border: none;")
    except Exception:
        pass