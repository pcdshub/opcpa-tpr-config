from __future__ import annotations

import logging
from os import path

import yaml
from pydm import Display
from pydm import widgets as pydm_widgets
from qtpy import QtWidgets
from xpm_prog import allowed_goose_rates, carbide_factors, make_base_rates

logger = logging.getLogger(__name__)


class UserConfigDisplay(Display):
    """
    Class for rep. rate configuration application user display.
    """

    # Top level widgets
    screen_title: pydm_widgets.PyDMLabel

    # Laser configuration widgets
    on_time_ec_rbv: pydm_widgets.PyDMLabel
    on_time_rate_rbv: pydm_widgets.PyDMLabel
    off_time_ec_rbv: pydm_widgets.PyDMLabel
    off_time_rate_rbv: pydm_widgets.PyDMLabel

    total_rate_box: QtWidgets.QComboBox
    goose_rate_box: QtWidgets.QComboBox
    goose_arrival_box: QtWidgets.QComboBox

    apply_button: QtWidgets.QPushButton

    # SC metadata widgets
    pattern_name_label: QtWidgets.QLabel
    pattern_name_rbv: pydm_widgets.PyDMLabel

    rate_label: QtWidgets.QLabel
    rate_rbv: pydm_widgets.PyDMLabel

    time_source_label: QtWidgets.QLabel
    time_source_rbv: pydm_widgets.PyDMLabel

    offset_label: QtWidgets.QLabel
    offset_rbv: pydm_widgets.PyDMLabel

    time_slot_label: QtWidgets.QLabel
    time_slot_rbv: pydm_widgets.PyDMLabel

    time_slot_mask_label: QtWidgets.QLabel
    time_slot_mask_rbv: pydm_widgets.PyDMLabel

    def __init__(
        self,
        parent=None,
        config: str = "",
        db: str = "",
        debug: bool = False,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self._debug = debug

        self.read_config(config)

        if self._config is None:
            raise ValueError(f"Could not read config file {config}")

        if self._debug:
            print(f"Read configuration file: {config}")
            cfg_keys = self._config.keys()
            print(f"Configuration sections: {cfg_keys}")
            print(self._config)

        self.screen_title.setText(self._config['main']['title'])

        self.update_pvs()

        self._base_rates = make_base_rates(carbide_factors)

        self.update_base_rates()
        self.update_goose_rates()
        self.update_goose_arrival()

        self.total_rate_box.currentTextChanged.connect(self.update_goose_rates)

        self.apply_button.clicked.connect(self.apply_config)

    def ui_filename(self):
        return "user_config.ui"

    def ui_filepath(self):
        return path.join(
            path.dirname(path.realpath(__file__)), self.ui_filename()
        )

    def read_config(self, config_file):
        """
        Read in the config file for the screen.
        """
        with open(config_file, "r") as f:
            conf = yaml.safe_load(f)
        self._config = conf

    def update_pvs(self):
        """
        Modify RBV widgets to use the PV(s) specified in the config file.
        """
        # Event code data
        self._on_time = self._config['main']['on_time_ec']
        self._off_time = self._config['main']['off_time_ec']

        self.on_time_ec_rbv.setText(self._on_time)
        self.off_time_ec_rbv.setText(self._off_time)

        if self._debug:
            print(f"On time EC: {self._on_time}")
            print(f"Off time EC: {self._off_time}")

        # TODO: Figure out how to index out the sequence engine rate values

        # SC metadata
        sc_base = self._config['main']['meta_pv']

        if self._debug:
            print(f"SC metadata base PV: {sc_base}")

        self.pattern_name_rbv.set_channel(f"ca://{sc_base}:NAME")
        self.rate_rbv.set_channel(f"ca://{sc_base}:RATE_RBV")
        self.time_source_rbv.set_channel(f"ca://{sc_base}:TIME_SRC")
        self.offset_rbv.set_channel(f"ca://{sc_base}:OFFSET_RBV")
        self.time_slot_rbv.set_channel(f"ca://{sc_base}:TS")
        self.time_slot_mask_rbv.set_channel(f"ca://{sc_base}:TSMASK")

    def update_base_rates(self):
        if self._base_rates is not None:
            for rate in self._base_rates:
                self.total_rate_box.addItem(str(rate))
            if self._debug:
                print(f"Allowed base rates: {self._base_rates}")

    @property
    def base_rate(self):
        return int(self.total_rate_box.currentText())

    def update_goose_rates(self):
        if self._base_rates is not None:
            goose_rates = allowed_goose_rates(
                self.base_rate,
                self._base_rates
            )
            self.goose_rate_box.clear()
            for rate in goose_rates:
                self.goose_rate_box.addItem(str(rate))
            if self._debug:
                print(f"Requested base rate: {rate}")
                print(f"Allowed goose rates: {goose_rates}")

    @property
    def goose_rate(self):
        return int(self.goose_rate_box.currentText())

    def update_goose_arrival(self):
        cfgs = self._config['goose_arrival_configs']
        if cfgs is not None:
            if self._debug:
                print(f"Goose arrival configs: {cfgs}")
            for name, cfg in cfgs.items():
                text = cfg['desc']
                cfg.pop('desc', None)
                self.goose_arrival_box.addItem(
                    text,
                    userData=cfg
                )

    @property
    def arrival_config(self):
        return self.goose_arrival_box.currentData()

    def apply_config(self):
        """
        Apply the requested configuration to the system.
        """
        if self._debug:
            print(f"Base rate: {self.base_rate}")
            print(f"Goose rate: {self.goose_rate}")
            print(f"Goose arrival: {self.arrival_config}")
