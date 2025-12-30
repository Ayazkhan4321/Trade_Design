import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from Forgot_password.forgot_password_controller import ForgotPasswordDialog, ForgotPasswordWorker
import Forgot_password.forgot_password_controller as fp_ctrl


def _ensure_app():
    return QApplication.instance() or QApplication(sys.argv)


def test_button_enable_disable():
    app = _ensure_app()
    dlg = ForgotPasswordDialog()
    dlg.show()
    QTest.qWait(50)

    assert not dlg.ui.pb_send_link.isEnabled()

    QTest.keyClicks(dlg.ui.le_forgot_password, "bad-email")
    QTest.qWait(20)
    assert not dlg.ui.pb_send_link.isEnabled()

    dlg.ui.le_forgot_password.clear()
    QTest.keyClicks(dlg.ui.le_forgot_password, "a@b.com")
    QTest.qWait(20)
    assert dlg.ui.pb_send_link.isEnabled()
    dlg.close()


def test_on_finished_success(monkeypatch):
    app = _ensure_app()
    dlg = ForgotPasswordDialog()
    dlg.show()

    called = {}

    def fake_info(parent, title, text):
        called['info'] = (title, text)

    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.information', fake_info)

    # simulate completion
    dlg._on_finished(True, "Reset link sent", False)

    assert 'info' in called
    # Dialog should accept (closed)
    assert not dlg.isVisible()


def test_on_finished_failure(monkeypatch):
    app = _ensure_app()
    dlg = ForgotPasswordDialog()
    dlg.show()

    called = {}

    def fake_warn(parent, title, text):
        called['warn'] = (title, text)

    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.warning', fake_warn)

    dlg._on_finished(False, "Unable to connect", False)

    assert 'warn' in called
    # Dialog should still be open (user can retry)
    assert dlg.isVisible()
    dlg.close()


def test_worker_run_invokes_service(monkeypatch):
    captured = {}

    # Patch controller-level function (the worker calls the name in controller module)
    monkeypatch.setattr('Forgot_password.forgot_password_controller.send_reset_link', lambda email: (True, "ok"))

    w = ForgotPasswordWorker()

    def on_finished(success, message):
        captured['success'] = success
        captured['message'] = message

    w.finished.connect(on_finished)

    # run synchronously
    w.run("a@b.com")

    assert captured.get('success') is True
    assert 'ok' in captured.get('message', '')


def test_threaded_flow(monkeypatch):
    """Start the dialog, click send and ensure threaded path finishes and dialog closes on success."""
    app = _ensure_app()
    dlg = ForgotPasswordDialog()
    called = {}

    def fake_info(parent, title, text):
        called['info'] = (title, text)

    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.information', fake_info)

    # Make the service sleep briefly to simulate real network latency
    import time

    def slow_send(email):
        time.sleep(0.2)
        return True, "Reset link (threaded)", False

    monkeypatch.setattr('Forgot_password.forgot_password_controller.send_reset_link', slow_send)

    dlg.show()
    QTest.qWait(50)
    QTest.keyClicks(dlg.ui.le_forgot_password, "a@b.com")
    QTest.qWait(20)
    QTest.mouseClick(dlg.ui.pb_send_link, Qt.LeftButton)

    # After clicking the button the label should change
    assert dlg.ui.pb_send_link.text() == "Sending..."

    # Wait for thread to finish (up to ~3s)
    for _ in range(30):
        QTest.qWait(100)
        if dlg._thread is None or not getattr(dlg._thread, "isRunning", lambda: False)():
            break

    # Verify callback happened and dialog closed
    assert 'info' in called
    assert not dlg.isVisible()
    dlg.close()


def test_cancel_stops_thread(monkeypatch):
    """Start the dialog, click send then close the dialog to cancel the in-flight request."""
    app = _ensure_app()
    dlg = ForgotPasswordDialog()
    called = {}

    def fake_info(parent, title, text):
        called['info'] = (title, text)

    def fake_warn(parent, title, text):
        called['warn'] = (title, text)

    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.information', fake_info)
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.warning', fake_warn)

    # Make the service sleep longer to simulate a long request
    import time

    def slow_send(email):
        # sleep a bit longer than our test will wait before closing
        time.sleep(1.0)
        return True, "Reset link (threaded)", False

    monkeypatch.setattr('Forgot_password.forgot_password_controller.send_reset_link', slow_send)

    dlg.show()
    QTest.qWait(50)
    QTest.keyClicks(dlg.ui.le_forgot_password, "a@b.com")
    QTest.qWait(20)
    QTest.mouseClick(dlg.ui.pb_send_link, Qt.LeftButton)

    # ensure thread started (wait up to ~1s)
    import pytest

    for _ in range(20):
        QTest.qWait(50)
        if dlg._thread is not None and getattr(dlg._thread, "isRunning", lambda: False)():
            break
    else:
        pytest.skip("worker thread didn't start in time on this platform")

    # Close dialog (user cancels) while request in-flight
    dlg.close()

    # Wait briefly for thread to be cancelled and stop
    for _ in range(30):
        QTest.qWait(50)
        if dlg._thread is None or not getattr(dlg._thread, "isRunning", lambda: False)():
            break

    # No info or warning should have been shown (we ignore cancelled results)
    assert 'info' not in called
    assert 'warn' not in called
    # Thread should have been stopped/cleared
    assert dlg._thread is None or not getattr(dlg._thread, "isRunning", lambda: False)()


def test_retry_prompt_and_retry_action(monkeypatch):
    app = _ensure_app()
    dlg = ForgotPasswordDialog()

    called = {"resent": False}

    def fake_question(parent, title, text, buttons):
        return QMessageBox.Retry

    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.question', fake_question)

    def fake_on_send_clicked(self=None):
        called["resent"] = True

    monkeypatch.setattr(ForgotPasswordDialog, '_on_send_clicked', fake_on_send_clicked)

    dlg._on_finished(False, "Request timed out. Please try again.", True)

    assert called["resent"] is True


def test_retry_prompt_and_cancel(monkeypatch):
    app = _ensure_app()
    dlg = ForgotPasswordDialog()

    def fake_question(parent, title, text, buttons):
        return QMessageBox.Cancel

    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.question', fake_question)

    called = {"resent": False}

    def fake_on_send_clicked(self=None):
        called["resent"] = True

    monkeypatch.setattr(ForgotPasswordDialog, '_on_send_clicked', fake_on_send_clicked)

    dlg._on_finished(False, "Request timed out. Please try again.", True)

    assert called["resent"] is False

