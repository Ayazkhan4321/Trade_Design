"""Manual-ish test for Forgot Password dialog

Run this locally to exercise the dialog quickly. It patches `send_reset_link`
and `QMessageBox` so the test runs without network or modal blocking.

Usage: python scripts/manual_forgot_test.py
"""
import sys
import os
import time
# Ensure repo root is importable when running this script directly
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from Forgot_password.forgot_password_controller import ForgotPasswordDialog


def run_test_case(fake_send_return):
    app = QApplication.instance() or QApplication(sys.argv)
    dlg = ForgotPasswordDialog()

    # Patch controller-level send_reset_link (the worker calls the name from the controller module)
    import Forgot_password.forgot_password_controller as fp_ctrl
    orig_send = fp_ctrl.send_reset_link
    fp_ctrl.send_reset_link = lambda email: fake_send_return

    # Patch QMessageBox to print instead of showing modals
    orig_info = QMessageBox.information
    orig_warn = QMessageBox.warning
    QMessageBox.information = lambda parent, title, text: print("INFO:", title, text)
    QMessageBox.warning = lambda parent, title, text: print("WARN:", title, text)

    dlg.show()
    QTest.qWait(50)

    # Enter email and click
    QTest.keyClicks(dlg.ui.le_forgot_password, "a@b.com")
    QTest.qWait(50)
    print("Button enabled after valid email:", dlg.ui.pb_send_link.isEnabled())
    QTest.mouseClick(dlg.ui.pb_send_link, Qt.LeftButton)

    # Wait for worker thread to finish (up to ~2s)
    for _ in range(20):
        QTest.qWait(100)
        if dlg._thread is None or not getattr(dlg._thread, "isRunning", lambda: False)():
            break

    # If still running, ask it to quit and wait a bit more
    if dlg._thread is not None and getattr(dlg._thread, "isRunning", lambda: False)():
        try:
            dlg._thread.quit()
        except Exception:
            pass
        for _ in range(20):
            QTest.qWait(100)
            if not getattr(dlg._thread, "isRunning", lambda: False)():
                break
        # Try a blocking wait for the thread to finish (safer on shutdown)
        try:
            dlg._thread.wait(2000)
        except Exception:
            pass

    # Restore
    fp_ctrl.send_reset_link = orig_send
    QMessageBox.information = orig_info
    QMessageBox.warning = orig_warn
    dlg.close()


if __name__ == "__main__":
    print("== Success path ==")
    run_test_case((True, "Reset link sent"))
    time.sleep(0.5)
    print("== Failure path ==")
    run_test_case((False, "Unable to connect"))
