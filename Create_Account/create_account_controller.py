"""UI controller for Create Account feature.

Implements background workers for country loading and account creation and keeps
UI wiring and validation centralized and testable.
"""
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta

from PySide6.QtWidgets import QDialog, QMessageBox, QPushButton, QLabel
from PySide6.QtCore import QObject, Signal, QThread, Qt, QTimer
from .create_account_ui import Ui_create_account
from .create_account_service import create_account, get_countries, CreateAccountRequest, verify_otp
from . import create_account_style as style

logger = logging.getLogger(__name__)


def format_issue_times(client_dt: datetime, server_iso: Optional[str]) -> str:
    """Return a short human string showing client send time and server-created time (if any)."""
    try:
        client_str = client_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        client_str = client_dt.isoformat()

    server_part = ""
    if server_iso:
        try:
            s = server_iso
            if s.endswith('Z'):
                s = s.replace('Z', '+00:00')
            sd = datetime.fromisoformat(s)
            # convert to local tz
            sd_local = sd.astimezone()
            try:
                server_str = sd_local.strftime("%Y-%m-%d %H:%M:%S %Z")
            except Exception:
                server_str = sd_local.isoformat()
            server_part = f"Server created at: {server_str}."
        except Exception:
            server_part = f"Server time: {server_iso}"

    parts = [f"Sent (local): {client_str}."]
    if server_part:
        parts.append(server_part)
    parts.append("Note: your mailbox may display a different timezone; if OTP appears expired, use Resend.")
    return " ".join(parts)


class CountriesWorker(QObject):
    finished = Signal(bool, object, bool)  # success, data_or_message, retryable

    def run(self) -> None:
        success, data, retryable = get_countries()
        self.finished.emit(success, data, retryable)


class CreateAccountWorker(QObject):
    # Emit (success, message, retryable, optional_data)
    finished = Signal(bool, str, bool, object)

    def run(self, payload: CreateAccountRequest) -> None:
        try:
            # Request creation and ask for the server data to be returned when available
            res = create_account(payload, include_data=True)
            # Support both (success, message, retryable) and (success, message, retryable, data)
            if isinstance(res, tuple) and len(res) == 3:
                success, message, retryable = res
                data = None
            elif isinstance(res, tuple) and len(res) == 4:
                success, message, retryable, data = res
            else:
                success, message = res
                retryable = False
                data = None
            self.finished.emit(success, message, retryable, data)
        except Exception:
            logger.exception("Exception in CreateAccountWorker")
            self.finished.emit(False, "Unexpected error occurred.", True, None)


class VerifyWorker(QObject):
    """Worker to verify code only."""

    finished = Signal(bool, str, bool)

    def __init__(self) -> None:
        super().__init__()
        self._cancelled = False

    def run(self, identifier: str, code: str, account_type_id: Optional[int] = None) -> None:
        """Verify the code only. Emits the verify result."""
        if self._cancelled:
            self.finished.emit(False, "Cancelled", False)
            return
        try:
            vres = verify_otp(identifier, code, account_type_id)
            if isinstance(vres, tuple) and len(vres) == 3:
                v_success, v_message, v_retry = vres
            else:
                v_success, v_message = vres
                v_retry = False

            if self._cancelled:
                self.finished.emit(False, "Cancelled", False)
                return

            if v_success:
                self.finished.emit(True, v_message, False)
            else:
                self.finished.emit(False, v_message, v_retry)

        except Exception:
            logger.exception("Exception in VerifyWorker")
            self.finished.emit(False, "Unexpected error occurred.", True)

    def cancel(self) -> None:
        self._cancelled = True


class CreateAccountDialog(QDialog):
    def __init__(self, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.ui = Ui_create_account()
        self.ui.setupUi(self)

        # Apply styles (best-effort)
        try:
            style.apply_create_account_styles(self.ui, self)
        except Exception:
            # ignore and continue
            pass

        # Make dialog match the Designer window title/size and center on parent
        try:
            self.setWindowTitle("Create Account")
            self.setMinimumSize(457, 358)
            if parent is not None:
                try:
                    parent_center = parent.frameGeometry().center()
                    self.move(parent_center - self.rect().center())
                except Exception:
                    pass
        except Exception:
            pass

        # initial state
        self.ui.pb_continue_verify.setEnabled(False)
        self.ui.cmb_country_code.addItem("Loading...")
        self.ui.cmb_country_code.setEnabled(False)

        # wire signals
        self.ui.le_first_name.textChanged.connect(self._on_input_changed)
        self.ui.le_last_name.textChanged.connect(self._on_input_changed)
        self.ui.le_number.textChanged.connect(self._on_input_changed)
        self.ui.cb_terms_privacy_policy.stateChanged.connect(self._on_input_changed)
        self.ui.pb_continue_verify.clicked.connect(self._on_continue_clicked)
        self.ui.lb_signin.mousePressEvent = lambda event: self.reject()

        # verification page controls (initially disabled)
        try:
            self.ui.pb_verify.setEnabled(False)
            self.ui.pb_verify.setCursor(Qt.ForbiddenCursor)
            self.ui.le_code.textChanged.connect(self._on_code_changed)
            self.ui.pb_verify.clicked.connect(self._on_verify_clicked)
            self.ui.pb_back.clicked.connect(lambda: self._go_back_to_registration())
        except Exception:
            # If UI was not updated in Designer, ignore
            pass

        # enforce single selection for account type buttons
        for btn_name in ("pb_classic", "pb_ecn", "pb_premium", "pb_other"):
            btn = getattr(self.ui, btn_name)
            btn.clicked.connect(self._on_account_type_clicked)

        # Thread placeholders (separate threads for create, send, and verify to avoid conflicts)
        self._create_thread: Optional[QThread] = None
        self._create_worker: Optional[QObject] = None
        self._send_thread: Optional[QThread] = None
        self._send_worker: Optional[QObject] = None
        # verify worker placeholders
        self._verify_thread: Optional[QThread] = None
        self._verify_worker: Optional[QObject] = None

        # created account data (if server returned it)
        self._created_user_id: Optional[int] = None
        self._created_user_data: Optional[dict] = None

        # OTP countdown and resend bookkeeping
        self._last_send_time: Optional[datetime] = None
        self._otp_ttl_seconds: int = 180  # default 3 minutes
        self._otp_timer: Optional[QTimer] = None
        self._server_expiry: Optional[datetime] = None
        # small slack to add to TTL to mitigate minor mailbox timestamp skews (seconds)
        self._otp_ttl_slack_seconds: int = 60
        self._resend_initiated: bool = False
        self._prev_slack: Optional[int] = None
        self._remaining_seconds_label_name = 'lb_otp_remaining'

        # Start loading countries
        self._start_load_countries()

    def _on_account_type_clicked(self) -> None:
        # ensure only the clicked button is checked
        for btn_name in ("pb_classic", "pb_ecn", "pb_premium", "pb_other"):
            btn = getattr(self.ui, btn_name)
            if self.sender() is btn:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        self._on_input_changed()

    def _on_input_changed(self, *args) -> None:
        # Enable continue button only when required fields are present and terms accepted
        first = self.ui.le_first_name.text().strip()
        last = self.ui.le_last_name.text().strip()
        number = self.ui.le_number.text().strip()
        terms = self.ui.cb_terms_privacy_policy.isChecked()
        account_type_selected = any(getattr(self.ui, name).isChecked() for name in ("pb_classic", "pb_ecn", "pb_premium", "pb_other"))

        if first and last and number and terms and account_type_selected:
            self.ui.pb_continue_verify.setEnabled(True)
            self.ui.pb_continue_verify.setCursor(Qt.PointingHandCursor)
        else:
            self.ui.pb_continue_verify.setEnabled(False)
            self.ui.pb_continue_verify.setCursor(Qt.ForbiddenCursor)

    def _start_load_countries(self) -> None:
        self._countries_thread = QThread()
        self._countries_thread.setObjectName("CreateAccountCountriesThread")
        self._countries_worker = CountriesWorker()
        self._countries_worker.moveToThread(self._countries_thread)
        self._countries_thread.started.connect(lambda: self._countries_worker.run())
        self._countries_worker.finished.connect(self._on_countries_loaded)
        self._countries_worker.finished.connect(self._countries_thread.quit)
        self._countries_worker.finished.connect(self._countries_worker.deleteLater)
        self._countries_thread.finished.connect(self._countries_thread.deleteLater)
        self._countries_thread.start()

    def _on_countries_loaded(self, success: bool, data, retryable: bool) -> None:
        # Use the dedicated country utils to format/store combo entries
        from .country_utils import format_country_display, normalize_country_data

        self.ui.cmb_country_code.clear()
        if success and isinstance(data, list):
            added = False
            for c in data:
                normalized = normalize_country_data(c) if isinstance(c, dict) else None
                if normalized is None:
                    # Skip malformed entries
                    continue
                display = format_country_display(normalized)
                self.ui.cmb_country_code.addItem(display, normalized)
                added = True

            if added:
                self.ui.cmb_country_code.setEnabled(True)
                return

        # Fallback if nothing usable was added
        fallback = {"name": "United States", "dial_code": "+1", "code": "US"}
        self.ui.cmb_country_code.addItem(format_country_display(fallback), fallback)
        self.ui.cmb_country_code.setEnabled(True)

        if not success:
            if retryable:
                QMessageBox.warning(self, "Countries", f"{data}\nYou can retry by reopening the dialog.")
            else:
                QMessageBox.warning(self, "Countries", str(data))

    def _on_continue_clicked(self) -> None:
        # Validate again
        first = self.ui.le_first_name.text().strip()
        last = self.ui.le_last_name.text().strip()
        number = self.ui.le_number.text().strip()
        referral = self.ui.le_refferal_code.text().strip() or None
        # email may not exist in UI; be permissive
        email = getattr(self.ui, "le_email", None)
        email_val = email.text().strip() if email is not None else None

        # Log click and payload for debugging
        logger.debug("Create account requested for email=%s phone=%s", email_val, number)

        # account type mapping
        account_map = {
            "pb_classic": 1,
            "pb_ecn": 2,
            "pb_premium": 3,
            "pb_other": 4,
        }
        selected = None
        for name, idx in account_map.items():
            btn = getattr(self.ui, name)
            if btn.isChecked():
                selected = idx
                break

        creation_type = "Live" if self.ui.Live_Demo_tab.currentIndex() == 0 else "Demo"

        country_data = None
        current_index = self.ui.cmb_country_code.currentIndex()
        if current_index >= 0:
            country_data = self.ui.cmb_country_code.itemData(current_index)

        # Build payload for account creation now (account will be created BEFORE verification)
        payload = CreateAccountRequest(
            firstName=first,
            lastName=last,
            email=email_val,
            phone=number,
            accountTypeID=selected,
            creationType=creation_type,
            referralCode=referral,
            country=country_data,
        )

        # Require an email address for verification; do not send to phone
        if not email_val:
            QMessageBox.warning(self, "Email required", "Please enter an email address to receive the verification code.")
            return

        # disable UI while request runs
        self.ui.pb_continue_verify.setEnabled(False)
        self.ui.pb_continue_verify.setText("Creating...")

        # Start a create-account worker thread (create user in DB, but DO NOT show success to user here)
        self._create_thread = QThread()
        self._create_thread.setObjectName("CreateAccountThread")
        self._create_worker = CreateAccountWorker()
        self._create_worker.moveToThread(self._create_thread)
        self._create_thread.started.connect(lambda: self._create_worker.run(payload))
        # connect to a dedicated handler that will proceed to send verification on success
        self._create_worker.finished.connect(self._on_create_finished)
        # Note: _on_create_finished now receives optional data parameter from worker
        self._create_worker.finished.connect(self._create_thread.quit)
        self._create_worker.finished.connect(self._create_worker.deleteLater)
        self._create_thread.finished.connect(self._on_create_thread_finished)
        self._create_thread.finished.connect(self._create_thread.deleteLater)
        self._create_thread.start()

    def _on_send_finished(self, success: bool, message: str, retryable: bool, data: object = None) -> None:
        # Called when the send-verification request completes
        logger.debug("_on_send_finished called: success=%s message=%s retryable=%s data=%s", success, message, retryable, bool(data))
        # Normalize message to string to avoid type issues in QMessageBox
        try:
            message_text = str(message) if message is not None else ""
        except Exception:
            message_text = ""

        self.ui.pb_continue_verify.setEnabled(True)
        self.ui.pb_continue_verify.setText("Continue to Verification")

        if success:
            logger.info("Verification email successfully sent to %s", self.ui.le_email.text().strip() if getattr(self.ui, 'le_email', None) is not None else '<unknown>')

            # Switch to verification page and focus the code input first so it's visible
            try:
                self.ui.stackedWidget.setCurrentIndex(1)
                # Force UI update and ensure dialog is raised so the user sees page 2
                try:
                    from PySide6.QtWidgets import QApplication
                    QApplication.processEvents()
                except Exception:
                    pass
                try:
                    self.raise_()
                    self.activateWindow()
                    self.ui.stackedWidget.repaint()
                except Exception:
                    logger.exception("Failed to raise or repaint verification dialog")
                logger.debug("Switched to stackedWidget index=%s", self.ui.stackedWidget.currentIndex())
            except Exception:
                logger.exception("Failed to set stackedWidget to verification page")

            # Keep Designer labels unchanged — do not overwrite title/step text from the .ui file
            try:
                # Intentionally no-op: preserve the labels and layout authored in Designer
                pass
            except Exception:
                logger.exception("Skipped updating verification label to preserve Designer layout")

            # add or enable resend button on verification page
            try:
                if not hasattr(self.ui, 'pb_resend'):
                    self.ui.pb_resend = QPushButton("Resend code", self.ui.stackedWidget.widget(1))
                    # place button below the verify/back buttons when possible
                    try:
                        self.ui.pb_resend.setGeometry(self.ui.pb_back.geometry().x(), self.ui.pb_back.geometry().y() + 40, 140, 24)
                    except Exception:
                        pass
                    self.ui.pb_resend.clicked.connect(self._on_resend_clicked)
                # Disable resend until the TTL has expired to avoid rapid resends
                self.ui.pb_resend.setEnabled(False)
                self.ui.pb_resend.setText("Resend code")
            except Exception:
                logger.exception("Failed to add or enable resend button")

            # enable / prepare the code input
            try:
                self.ui.le_code.setEnabled(True)
                self.ui.le_code.setFocus()
                self.ui.pb_verify.setEnabled(False)
                self.ui.pb_verify.setCursor(Qt.ForbiddenCursor)
                # start OTP countdown timer (prefer server timestamp when available)
                try:
                    # compute server timestamp if present in response data or created user data
                    server_dt_iso = None
                    try:
                        if isinstance(data, dict):
                            server_dt_iso = data.get('createdAt') or (data.get('data', {}) or {}).get('createdAt')
                    except Exception:
                        server_dt_iso = None
                    try:
                        if not server_dt_iso:
                            server_dt_iso = self._created_user_data.get('createdAt') if isinstance(self._created_user_data, dict) else None
                    except Exception:
                        server_dt_iso = None

                    self._start_otp_timer(server_dt_iso)
                except Exception:
                    logger.exception("Failed to start OTP timer on send finished")
            except Exception:
                logger.exception("Failed to enable verification controls")

            # Finally, show a confirmation dialog (this may block but page is already visible)
            try:
                # If resend was used, surface a short note that TTL was extended
                if getattr(self, '_resend_initiated', False):
                    try:
                        QMessageBox.information(self, "Verification resent", f"{message_text}\n\nTTL extended temporarily to accommodate mailbox timestamp skew.")
                    except Exception:
                        QMessageBox.information(self, "Verification sent", message_text)
                else:
                    QMessageBox.information(self, "Verification sent", message_text)
            except Exception:
                logger.exception("Failed to show verification info dialog")

            # if we adjusted slack for resend, revert to previous value after starting the timer
            try:
                if getattr(self, '_resend_initiated', False):
                    self._resend_initiated = False
                    try:
                        if self._prev_slack is not None:
                            self._otp_ttl_slack_seconds = self._prev_slack
                    except Exception:
                        pass
                    finally:
                        self._prev_slack = None
            except Exception:
                pass
        else:
            logger.warning("Failed to send verification email to %s: %s", self.ui.le_email.text().strip() if getattr(self.ui, 'le_email', None) is not None else '<unknown>', message_text)
            # Re-enable continue button to allow retry or correction
            self.ui.pb_continue_verify.setEnabled(True)
            self.ui.pb_continue_verify.setText("Continue to Verification")
            if retryable:
                choice = QMessageBox.question(self, "Failed to send verification", f"{message_text}\n\nWould you like to retry?", QMessageBox.Retry | QMessageBox.Cancel)
                if choice == QMessageBox.Retry:
                    self._on_continue_clicked()
            else:
                QMessageBox.warning(self, "Failed", message_text)

    def _on_create_finished(self, success: bool, message: str, retryable: bool, data: object = None) -> None:
        # Called when the initial create-account request completes. If creation succeeded,
        # proceed to send verification email (do NOT show account-created message here).
        if success:
            # store created user id and server data (createdAt etc.) so verify step can use it
            try:
                if isinstance(data, dict) and 'id' in data:
                    self._created_user_id = data.get('id')
                    # store the whole dict for timestamp lookup
                    self._created_user_data = data
                else:
                    self._created_user_id = None
                    self._created_user_data = None
            except Exception:
                self._created_user_id = None
                self._created_user_data = None

            # proceed to send verification to the created account
            email_text = self.ui.le_email.text().strip() if getattr(self.ui, 'le_email', None) is not None else ''
            logger.info("Account created on server; sending verification to %s (user_id=%s)", email_text or '<unknown>', getattr(self, '_created_user_id', None))
            try:
                # start send-verification using JSON payload to satisfy server
                contact_payload = {"email": email_text}
                # reuse send flow
                self.ui.pb_continue_verify.setEnabled(False)
                self.ui.pb_continue_verify.setText("Sending...")

                self._send_thread = QThread()
                self._send_thread.setObjectName("SendVerificationThread")
                class _SendWorker(QObject):
                    finished = Signal(bool, str, bool, object)
                    def run(self, payload_value):
                        try:
                            from .create_account_service import send_verification
                            res = send_verification(payload_value)
                            if isinstance(res, tuple) and len(res) == 3:
                                self.finished.emit(res[0], res[1], res[2], None)
                            elif isinstance(res, tuple) and len(res) == 4:
                                self.finished.emit(res[0], res[1], res[2], res[3])
                            else:
                                self.finished.emit(res[0], res[1], False, None)
                        except Exception:
                            logger.exception("Exception in SendWorker")
                            self.finished.emit(False, "Unexpected error occurred.", True, None)

                self._send_worker = _SendWorker()
                self._send_worker.moveToThread(self._send_thread)
                # pass only the contact payload (dict will be sent as JSON)
                self._send_thread.started.connect(lambda: self._send_worker.run(contact_payload))
                self._send_worker.finished.connect(self._on_send_finished)
                self._send_worker.finished.connect(self._send_thread.quit)
                self._send_worker.finished.connect(self._send_worker.deleteLater)
                self._send_thread.finished.connect(self._on_send_thread_finished)
                self._send_thread.finished.connect(self._send_thread.deleteLater)
                self._send_thread.start()
            except Exception:
                logger.exception("Exception while starting send-verification after create")
                QMessageBox.warning(self, "Failed", "Could not start verification request.")
                self.ui.pb_continue_verify.setEnabled(True)
                self.ui.pb_continue_verify.setText("Continue to Verification")
        else:
            # Creation failed — re-enable and surface message similar to previous flow
            self.ui.pb_continue_verify.setEnabled(True)
            self.ui.pb_continue_verify.setText("Continue to Verification")
            if retryable:
                choice = QMessageBox.question(self, "Failed to create account", f"{message}\n\nWould you like to retry?", QMessageBox.Retry | QMessageBox.Cancel)
                if choice == QMessageBox.Retry:
                    self._on_continue_clicked()
            else:
                QMessageBox.warning(self, "Failed", message)

    def _on_resend_clicked(self) -> None:
        # Called when user clicks 'Resend code' on verification page. This does not recreate the user.
        try:
            email_text = self.ui.le_email.text().strip() if getattr(self.ui, 'le_email', None) is not None else ''
            if not email_text:
                QMessageBox.warning(self, "Email required", "Please enter an email address to receive the verification code.")
                return
            contact_payload = {"email": email_text}

            # disable resend while request runs and make the resend be lenient (extra slack)
            try:
                if hasattr(self.ui, 'pb_resend'):
                    self.ui.pb_resend.setEnabled(False)
                    self.ui.pb_resend.setText("Resending...")
                # temporarily increase TTL slack to accommodate mailbox timestamp skew
                try:
                    self._prev_slack = self._otp_ttl_slack_seconds
                    self._otp_ttl_slack_seconds = max(self._otp_ttl_slack_seconds, 300)  # 5 minutes slack on resend
                    self._resend_initiated = True
                except Exception:
                    pass
            except Exception:
                pass

            self._send_thread = QThread()
            self._send_thread.setObjectName("SendVerificationThread")
            class _SendWorker(QObject):
                finished = Signal(bool, str, bool, object)
                def run(self, payload_value):
                    try:
                        from .create_account_service import send_verification
                        res = send_verification(payload_value)
                        if isinstance(res, tuple) and len(res) == 3:
                            self.finished.emit(res[0], res[1], res[2], None)
                        elif isinstance(res, tuple) and len(res) == 4:
                            self.finished.emit(res[0], res[1], res[2], res[3])
                        else:
                            self.finished.emit(res[0], res[1], False, None)
                    except Exception:
                        logger.exception("Exception in SendWorker")
                        self.finished.emit(False, "Unexpected error occurred.", True, None)

            self._send_worker = _SendWorker()
            self._send_worker.moveToThread(self._send_thread)
            self._send_thread.started.connect(lambda: self._send_worker.run(contact_payload))
            self._send_worker.finished.connect(self._on_send_finished)
            self._send_worker.finished.connect(self._send_thread.quit)
            self._send_worker.finished.connect(self._send_worker.deleteLater)
            self._send_thread.finished.connect(self._on_send_thread_finished)
            self._send_thread.finished.connect(self._send_thread.deleteLater)
            self._send_thread.start()
        except Exception:
            logger.exception("Failed to start resend request")
            QMessageBox.warning(self, "Failed", "Could not resend verification code.")
            try:
                if hasattr(self.ui, 'pb_resend'):
                    self.ui.pb_resend.setEnabled(True)
                    self.ui.pb_resend.setText("Resend code")
            except Exception:
                pass

    # OTP timer helpers -------------------------------------------------
    def _start_otp_timer(self, server_created_iso: Optional[str] = None) -> None:
        """Start or restart the OTP countdown timer and show remaining seconds.

        If `server_created_iso` is provided and parseable, the expiry will be computed
        from the server timestamp (server_created + TTL + slack). If the server time is in the
        future by a large amount, the expiry is clamped to now + TTL + slack to avoid confusing
        users with far-future mail timestamps.
        """
        try:
            # record local send time for display (make timezone-aware)
            self._last_send_time = datetime.now().astimezone()

            # try to compute server expiry if we received a server timestamp
            self._server_expiry = None
            if server_created_iso:
                try:
                    s = server_created_iso
                    if s.endswith('Z'):
                        s = s.replace('Z', '+00:00')
                    server_dt = datetime.fromisoformat(s)
                    # convert to UTC for arithmetic
                    server_dt_utc = server_dt.astimezone(timezone.utc)
                    now_utc = datetime.now(timezone.utc)
                    # Detect skew between server-created and local now (in seconds)
                    try:
                        skew_seconds = int((server_dt_utc.astimezone() - datetime.now().astimezone()).total_seconds())
                    except Exception:
                        skew_seconds = 0

                    # If there is a significant server-ahead skew, temporarily increase slack
                    extra_slack = self._otp_ttl_slack_seconds
                    try:
                        if skew_seconds > 60:
                            # add 10s buffer but cap to an upper bound (10 minutes)
                            extra_slack = min(max(self._otp_ttl_slack_seconds, skew_seconds + 10), 600)
                            logger.warning("Auto-extending OTP TTL by %s seconds due to server-client skew", extra_slack)
                            self._auto_extended_by = extra_slack
                        else:
                            self._auto_extended_by = 0
                    except Exception:
                        self._auto_extended_by = 0

                    expiry_utc = server_dt_utc + timedelta(seconds=(self._otp_ttl_seconds + extra_slack))
                    # Clamp expiry if it is unreasonably far in the future
                    max_allowed = now_utc + timedelta(seconds=(self._otp_ttl_seconds + extra_slack))
                    if expiry_utc > max_allowed:
                        expiry_utc = max_allowed
                    # store server expiry in local tz for display
                    self._server_expiry = expiry_utc.astimezone()
                except Exception:
                    logger.exception("Failed to parse server-created timestamp")
                    self._server_expiry = None

            # create label if missing
            if not hasattr(self.ui, self._remaining_seconds_label_name):
                lb = QLabel(self.ui.stackedWidget.widget(1))
                lb.setObjectName(self._remaining_seconds_label_name)
                lb.setStyleSheet('color: #333;')
                lb.setVisible(True)
                try:
                    # best-effort: add to existing verify layout
                    self.ui.verticalLayout_verify.addWidget(lb)
                except Exception:
                    lb.setVisible(True)
            else:
                lb = getattr(self.ui, self._remaining_seconds_label_name)
                lb.setVisible(True)

            # ensure any existing timer is stopped first
            self._stop_otp_timer()
            self._otp_timer = QTimer(self)
            self._otp_timer.setInterval(1000)
            self._otp_timer.timeout.connect(self._update_otp_timer)
            self._otp_timer.start()
            # restore verify button text (may have been set to expired previously)
            try:
                self.ui.pb_verify.setText("Verify & Continue to Login")
                self.ui.pb_verify.setCursor(Qt.ForbiddenCursor)
            except Exception:
                pass
            # run initial update
            self._update_otp_timer()
        except Exception:
            logger.exception("Failed to start OTP timer")

    def _stop_otp_timer(self) -> None:
        try:
            if self._otp_timer is not None:
                try:
                    self._otp_timer.stop()
                except Exception:
                    pass
                finally:
                    self._otp_timer = None
            # clear server expiry bookkeeping
            self._server_expiry = None
            if hasattr(self.ui, self._remaining_seconds_label_name):
                try:
                    getattr(self.ui, self._remaining_seconds_label_name).setVisible(False)
                except Exception:
                    pass
        except Exception:
            logger.exception("Failed to stop OTP timer")

    def _update_otp_timer(self) -> None:
        """Update the remaining time display and disable verification on expiry."""
        try:
            # If server expiry was provided prefer that for remaining computation
            now = datetime.now().astimezone()
            if self._server_expiry is not None:
                remaining = max(0, int((self._server_expiry - now).total_seconds()))
            else:
                if not self._last_send_time:
                    return
                elapsed = int((now - self._last_send_time).total_seconds())
                remaining = max(0, self._otp_ttl_seconds - elapsed)

            label = getattr(self.ui, self._remaining_seconds_label_name, None)
            if label is not None:
                mins, secs = divmod(remaining, 60)
                label.setText(f"Time remaining: {mins:02d}:{secs:02d}")
                label.setVisible(True)

            if remaining <= 0:
                # expired
                self._stop_otp_timer()
                try:
                    # disable verify and show prompt
                    self.ui.le_code.setEnabled(False)
                    self.ui.pb_verify.setEnabled(False)
                    self.ui.pb_verify.setText("Code expired")
                    if hasattr(self.ui, 'pb_resend'):
                        self.ui.pb_resend.setEnabled(True)
                        self.ui.pb_resend.setText("Resend code")
                except Exception:
                    pass
        except Exception:
            logger.exception("Error updating OTP timer")

    def _on_create_thread_finished(self) -> None:
        self._create_thread = None
        self._create_worker = None

    def _on_send_thread_finished(self) -> None:
        self._send_thread = None
        self._send_worker = None

    def _on_code_changed(self, text: str) -> None:
        # Enable verify button only when something is entered
        if text and text.strip():
            self.ui.pb_verify.setEnabled(True)
            self.ui.pb_verify.setCursor(Qt.PointingHandCursor)
        else:
            self.ui.pb_verify.setEnabled(False)
            self.ui.pb_verify.setCursor(Qt.ForbiddenCursor)

    def _on_verify_clicked(self) -> None:
        code = self.ui.le_code.text().strip()
        # basic validation
        if not code:
            QMessageBox.warning(self, "Invalid code", "Please enter the verification code.")
            return

        # disable controls while verifying
        self.ui.le_code.setEnabled(False)
        self.ui.pb_verify.setEnabled(False)
        self.ui.pb_verify.setText("Verifying...")

        # start verification worker thread
        self._verify_thread = QThread()
        self._verify_thread.setObjectName("CreateAccountVerifyThread")
        self._verify_worker = VerifyWorker()
        self._verify_worker.moveToThread(self._verify_thread)
        # Use the created user id if available, otherwise fall back to email
        identifier = None
        try:
            identifier = str(getattr(self, '_created_user_id')) if getattr(self, '_created_user_id', None) is not None else (self.ui.le_email.text().strip() if getattr(self.ui, 'le_email', None) is not None else '')
        except Exception:
            identifier = self.ui.le_email.text().strip() if getattr(self.ui, 'le_email', None) is not None else ''
        # Determine selected account type id for payload
        account_type_selected = None
        for name, idx in {"pb_classic":1, "pb_ecn":2, "pb_premium":3, "pb_other":4}.items():
            try:
                if getattr(self.ui, name).isChecked():
                    account_type_selected = idx
                    break
            except Exception:
                pass
        self._verify_thread.started.connect(lambda: self._verify_worker.run(identifier, code, account_type_selected))
        self._verify_worker.finished.connect(self._on_verify_finished)
        self._verify_worker.finished.connect(self._verify_thread.quit)
        self._verify_worker.finished.connect(self._verify_worker.deleteLater)
        self._verify_thread.finished.connect(self._on_verify_thread_finished)
        self._verify_thread.finished.connect(self._verify_thread.deleteLater)
        self._verify_thread.start()

    def _on_verify_finished(self, success: bool, message: str, retryable: bool) -> None:
        # Restore UI text-buttons
        self.ui.le_code.setEnabled(True)
        self.ui.pb_verify.setEnabled(True)
        self.ui.pb_verify.setText("Verify & Continue to Login")

        if success:
            # Stop OTP timer and show final account-created confirmation and close so caller can show login
            try:
                self._stop_otp_timer()
            except Exception:
                logger.exception("Failed to stop OTP timer on successful verify")
            QMessageBox.information(self, "Account created", message)
            self.accept()
        else:
            if retryable:
                choice = QMessageBox.question(self, "Verification failed", f"{message}\n\nWould you like to retry?", QMessageBox.Retry | QMessageBox.Cancel)
                if choice == QMessageBox.Retry:
                    self._on_verify_clicked()
            else:
                # Verification failed and server indicates not retryable — offer helpful actions.
                logger.warning("Verification failed (non-retryable): %s", message)
                # Present options: I have credentials (close and allow login), Resend code, or Cancel
                buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel
                choice = QMessageBox.question(self, "Verification result", f"{message}\n\nIf you received an email with your account credentials, click 'Yes' to proceed to login. Otherwise, click 'Retry' to try verifying again or 'Cancel' to stay on this page.", buttons)
                if choice == QMessageBox.StandardButton.Yes:
                    # Treat as verified for the user's convenience (they can login manually)
                    try:
                        self._stop_otp_timer()
                    except Exception:
                        pass
                    QMessageBox.information(self, "Account created", "Account verified or credentials received. You can now log in.")
                    self.accept()
                    return
                if choice == QMessageBox.StandardButton.Retry:
                    self._on_verify_clicked()
                # else Cancel -> stay on verification page

        self._verify_worker = None

    def _on_verify_thread_finished(self) -> None:
        self._verify_thread = None

    def _go_back_to_registration(self) -> None:
        try:
            self.ui.stackedWidget.setCurrentIndex(0)
        except Exception:
            pass

    def closeEvent(self, event) -> None:
        # If there were long-running threads, attempt cooperative shutdown (similar to forgot password)
        try:
            try:
                self._stop_otp_timer()
            except Exception:
                pass
            super().closeEvent(event)
        except Exception:
            logger.exception("Error during closeEvent")
