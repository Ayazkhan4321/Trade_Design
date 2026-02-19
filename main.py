import sys
from PySide6.QtWidgets import QApplication
from Main_window import MainWindow



import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

# Reduce verbosity of very noisy modules so payload dumps don't flood console.
# Keep global DEBUG for other components, but raise these specific loggers.
try:
    logging.getLogger('SymbolManager').setLevel(logging.INFO)
except Exception:
    pass
try:
    logging.getLogger('MarketWatch_jetfyx.services.market_data_service').setLevel(logging.WARNING)
except Exception:
    pass
try:
    logging.getLogger('SignalRCoreClient').setLevel(logging.WARNING)
except Exception:
    pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
