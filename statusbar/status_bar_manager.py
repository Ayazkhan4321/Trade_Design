from statusbar.help_block import HelpBlock
from statusbar.profile_block import ProfileBlock
from statusbar.datetime_block import DateTimeBlock
from statusbar.ohlcv_block import OHLCVBlock
from statusbar.signal_block import SignalBlock


class StatusBarManager:
    def __init__(self, status_bar):
        self.status_bar = status_bar

        self.help = HelpBlock()
        self.profile = ProfileBlock()
        self.datetime = DateTimeBlock()
        self.ohlcv = OHLCVBlock()
        self.signal = SignalBlock()

        self._add_widgets()

    def _add_widgets(self):
        self.status_bar.addWidget(self.help)
        self.status_bar.addWidget(self.profile)
        self.status_bar.addWidget(self.datetime)
        self.status_bar.addWidget(self.ohlcv, stretch=1)
        self.status_bar.addPermanentWidget(self.signal)

    # === External APIs ===
    def update_ohlcv(self, o, h, l, c, v):
        self.ohlcv.update_data(o, h, l, c, v)

    def clear_ohlcv(self):
        self.ohlcv.clear_data()

    def update_signal(self, text):
        self.signal.update_signal(text)
