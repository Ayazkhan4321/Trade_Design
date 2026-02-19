from typing import Dict, Optional

from PySide6.QtWidgets import QAbstractButton


class AccountTypeSelector:
    """Manage mutual-exclusive selection among multiple QPushButton-like widgets.

    Use `register(button, id_)` to register buttons and their associated account type id.
    Calling `get_selected()` returns the selected id or None.
    """

    def __init__(self) -> None:
        self._buttons: Dict[QAbstractButton, int] = {}

    def register(self, button: QAbstractButton, id_: int) -> None:
        try:
            # Ensure button acts like a toggle
            button.setCheckable(True)
        except Exception:
            pass

        self._buttons[button] = id_

        # connect to a stable handler capturing button object
        try:
            button.clicked.connect(lambda checked, b=button: self._on_clicked(b))
        except Exception:
            # fallback if click signal unavailable
            try:
                # try to connect to pressed
                button.pressed.connect(lambda b=button: self._on_clicked(b))
            except Exception:
                pass

    def _on_clicked(self, btn: QAbstractButton) -> None:
        # set clicked button checked and clear others
        for b in list(self._buttons.keys()):
            try:
                if b is btn:
                    b.setChecked(True)
                else:
                    b.setChecked(False)
            except Exception:
                pass

    def get_selected(self) -> Optional[int]:
        for b, id_ in self._buttons.items():
            try:
                if getattr(b, 'isChecked') and b.isChecked():
                    return id_
            except Exception:
                pass
        return None

    def clear(self) -> None:
        for b in list(self._buttons.keys()):
            try:
                b.setChecked(False)
            except Exception:
                pass
        self._buttons.clear()