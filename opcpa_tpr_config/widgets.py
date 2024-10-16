from __future__ import annotations

import logging
from os import path

import happi
import yaml
from pydm import Display
from pydm import widgets as pydm_widgets
from qtpy import QtWidgets
from xpm_prog import (allowed_goose_rates, carbide_factors, make_base_rates,
                      make_sequence)

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
    total_rate_label: QtWidgets.QLabel
    goose_rate_box: QtWidgets.QComboBox
    goose_rate_label: QtWidgets.QLabel
    goose_arrival_box: QtWidgets.QComboBox
    goose_arrival_label: QtWidgets.QLabel

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

    # Expert mode widgets
    expert_checkbox: QtWidgets.QCheckBox
    xpm_table: pydm_widgets.PyDMNTTable
    tpr_frame: QtWidgets.QFrame
    rbv_frame: QtWidgets.QFrame

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

        self._db = happi.Client(path=self._config['main']['laser_database'])

        if self._config is None:
            raise ValueError(f"Could not read config file {config}")

        if self._debug:
            print(f"Read configuration file: {config}")
            cfg_keys = self._config.keys()
            print(f"Configuration sections: {cfg_keys}")
            print(self._config)

        self.screen_title.setText(self._config['main']['title'])

        self.update_user_pvs()

        self._base_rates = make_base_rates(carbide_factors)

        self.update_base_rates()
        self.update_goose_rates()
        self.update_goose_arrival()

        self.configure_rbv_frames()

        self.update_expert_vis()

        self.update_goose_vis()

        self.total_rate_box.currentTextChanged.connect(self.update_goose_rates)

        self.apply_button.clicked.connect(self.apply_config)
        self.expert_checkbox.stateChanged.connect(self.update_expert_vis)

        self.goose_arrival_box.currentTextChanged.connect(
            self.update_goose_vis
        )

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

    @property
    def expert_mode(self):
        return self.expert_checkbox.isChecked()

    def update_expert_vis(self):
        """
        Update visibility of "expert mode" widgets based on expert mode check
        box status.
        """
        self.xpm_table.setVisible(self.expert_mode)
        self.tpr_frame.setVisible(self.expert_mode)
        self.rbv_frame.setVisible(self.expert_mode)

    def update_goose_vis(self):
        """
        Update visibility of goose rate control widget based on goose mode
        status.
        """
        self.goose_rate_box.setVisible(self.goose_enabled)
        self.goose_rate_label.setVisible(self.goose_enabled)

    def configure_rbv_frames(self):
        """
        Add a layout and widgets to the rbv frame based on the laser system
        happi database.
        """
        tpr_layout = QtWidgets.QGridLayout()
        tpr_layout = self.setup_tpr_rbvs(self._config, self._db, tpr_layout)
        self.tpr_frame.setLayout(tpr_layout)

        rbv_layout = QtWidgets.QGridLayout()
        rbv_layout = self.setup_signal_rbvs(self._config, self._db, rbv_layout)
        self.rbv_frame.setLayout(rbv_layout)

    def setup_tpr_rbvs(self, las_conf, las_db, grid):
        """
        Setup RBV widgets for TPR triggers associated with the laser system.

        Arguments
        ---------
        las_conf: The key name of the laser to be used.
        las_db: The file name of the laser happi db.json file
        grid: The QGridLayout widget to add widgets to
        """
        # Setup column headers
        desc = pydm_widgets.PyDMLabel()
        desc.setText("Trigger")
        grid.addWidget(desc, 0, 0)

        reprate = pydm_widgets.PyDMLabel()
        reprate.setText("Rep. Rate")
        grid.addWidget(reprate, 0, 1)

        ratemode = pydm_widgets.PyDMLabel()
        ratemode.setText("Rate Mode")
        grid.addWidget(ratemode, 0, 2)

        eventcode = pydm_widgets.PyDMLabel()
        eventcode.setText("Event Code")
        grid.addWidget(eventcode, 0, 3)

        width = pydm_widgets.PyDMLabel()
        width.setText("Width (ns)")
        grid.addWidget(width, 0, 4)

        delay = pydm_widgets.PyDMLabel()
        delay.setText("Delay (ns)")
        grid.addWidget(delay, 0, 5)

        op = pydm_widgets.PyDMLabel()
        op.setText("Logic")
        grid.addWidget(op, 0, 6)

        enabled = pydm_widgets.PyDMLabel()
        enabled.setText("Status")
        grid.addWidget(enabled, 0, 7)

        # Setup TPR PV RBVs
        tpr_trigs = las_db.search(device_class='pcdsdevices.tpr.TprTrigger')
        ntrig = 1
        for trig in tpr_trigs:
            if trig.metadata['active']:
                name = trig.metadata['name']
                if name in las_conf['main']['devices'].keys():
                    trig_conf = las_conf['main']['devices'][name]
                    rbvs = trig_conf['rbvs']
                    for nrbv, rbv in enumerate(rbvs):
                        child = self.configure_rbv_widget(trig, rbv)
                        grid.addWidget(child, ntrig, nrbv)
                    ntrig += 1

        return grid

    def setup_signal_rbvs(self, las_conf, las_db, grid):
        """
        Setup RBV widgets for TPR triggers associated with the laser system.

        Arguments
        ---------
        las_conf: The key name of the laser to be used.
        las_db: The file name of the laser happi db.json file
        grid: The QGridLayout widget to add widgets to
        """
        # Setup column headers
        desc = pydm_widgets.PyDMLabel()
        desc.setText("Signal")
        grid.addWidget(desc, 0, 0)

        val = pydm_widgets.PyDMLabel()
        val.setText("Value")
        grid.addWidget(val, 0, 1)

        # Setup Signal PV RBVs
        signals = las_db.search(device_class='ophyd.signal.EpicsSignal')
        nsig = 1
        for signal in signals:
            if signal.metadata['active']:
                name = signal.metadata['name']
                if name in las_conf['main']['devices'].keys():
                    sig_conf = las_conf['main']['devices'][name]
                    rbvs = sig_conf['rbvs']
                    for nrbv, rbv in enumerate(rbvs):
                        child = self.configure_rbv_widget(signal, rbv)
                        grid.addWidget(child, nsig, nrbv)
                    nsig += 1

        return grid

    def configure_rbv_widget(self, dev, rbv):
        """
        Setup a ophyd device RBV widget.

        Arguments
        ---------
        dev: happi Client search result
        rbv: The device class signal to create an RBV widget for
             *Note: in the case of EpicsSignals, we use a "val" to indicate
             that we want to use the base PV of the signal.

        returns:
            PyDMLabel
        """
        child = pydm_widgets.PyDMLabel()
        device = dev.get()
        if rbv == 'name':
            child.setText(getattr(device, 'name'))
            return child
        elif rbv == 'val':  # EpicsSignals need pvname, use "val" in config
            pvname = getattr(device, "pvname")
        else:
            pvname = getattr(device, f"{rbv}.pvname")
        channel = f"ca://{pvname}"
        child.set_channel(channel)

        return child

    def update_user_pvs(self):
        """
        Modify RBV widgets to use the PV(s) specified in the config file.
        """
        # Event code data
        self._engine = int(self._config['main']['engine'])
        on_time_idx = self._engine * 4
        off_time_idx = (self._engine * 4) + 1
        self._on_time = 256 + on_time_idx
        self._off_time = 256 + off_time_idx

        self.on_time_ec_rbv.setText(str(self._on_time))
        self.off_time_ec_rbv.setText(str(self._off_time))

        if self._debug:
            print(f"Engine: {self._engine}")
            print(f"On time EC: {self._on_time}")
            print(f"Off time EC: {self._off_time}")
            print(f"On time index: {on_time_idx}")
            print(f"Off time index: {off_time_idx}")

        # SC metadata
        sc_base = self._config['main']['meta_pv']
        xpm_pv = self._config['main']['xpm_pv']

        if self._debug:
            print(f"SC metadata base PV: {sc_base}")

        self.pattern_name_rbv.set_channel(f"ca://{sc_base}:NAME")
        self.rate_rbv.set_channel(f"ca://{sc_base}:RATE_RBV")
        self.time_source_rbv.set_channel(f"ca://{sc_base}:TIME_SRC")
        self.offset_rbv.set_channel(f"ca://{sc_base}:OFFSET_RBV")
        self.time_slot_rbv.set_channel(f"ca://{sc_base}:TS")
        self.time_slot_mask_rbv.set_channel(f"ca://{sc_base}:TSMASK")
        self.on_time_rate_rbv.set_channel(f"pva://{xpm_pv}/Rate/{on_time_idx}")
        self.off_time_rate_rbv.set_channel(
            f"pva://{xpm_pv}/Rate/{off_time_idx}"
        )

        self.xpm_table.set_channel(f"pva://{xpm_pv}")

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

    @property
    def goose_enabled(self):
        txt = self.goose_arrival_box.currentText()
        if txt != "Goose off":
            return True
        else:
            return False

    def apply_config(self):
        """
        Apply the requested configuration to the system.
        """
        base_div = 910000//self.base_rate
        if self.goose_enabled:
            goose_div = 910000//self.goose_rate
        else:
            goose_div = None

        # This is a float PV for some reason
        offset = int(self.offset_rbv.value)
        if offset == 0:
            offset = None

        if self._debug:
            print(f"Base rate: {self.base_rate}")
            print(f"Goose rate: {self.goose_rate}")
            print(f"Goose arrival: {self.arrival_config}")
            print(f"Base div: {base_div}")
            print(f"Goose div: {goose_div}")
            print(f"Offset: {offset}")

        instrset = make_sequence(base_div, goose_div, offset, self._debug)
        print(instrset)  # Make flake8 happy for now
