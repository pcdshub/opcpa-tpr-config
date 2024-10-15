from __future__ import annotations

import logging
from os import path

import yaml
from pydm import Display
from pydm import widgets as pydm_widgets
from qtpy import QtWidgets

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
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.read_config(config)

        if self._config is None:
            raise ValueError(f"Could not read config file {config}")

        self.screen_title.setText(self._config['main']['title'])

        self.update_pvs()

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
        self.on_time_ec_rbv.setText(self._config['main']['on_time_ec'])
        self.off_time_ec_rbv.setText(self._config['main']['off_time_ec'])

        # TODO: Figure out how to index out the sequence engine rate values

        # SC metadata
        sc_base = self._config['main']['meta_pv']
        self.pattern_name_rbv.set_channel(f"ca://{sc_base}:NAME")
        self.rate_rbv.set_channel(f"ca://{sc_base}:RATE_RBV")
        self.time_source_rbv.set_channel(f"ca://{sc_base}:TIME_SRC")
        self.offset_rbv.set_channel(f"ca://{sc_base}:OFFSET_RBV")
        self.time_slot_rbv.set_channel(f"ca://{sc_base}:TS")
        self.time_slot_mask_rbv.set_channel(f"ca://{sc_base}:TSMASK")
