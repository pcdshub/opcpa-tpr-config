from __future__ import annotations

import logging
import time
from os import path

import happi
import yaml
from ophyd import EpicsSignal
from pydm import Display
from pydm import widgets as pydm_widgets
from qtpy import QtWidgets
from xpm_prog import (allowed_goose_rates, build_base_sequence,
                      build_laser_sequence, make_possible_rates, nc_factors,
                      sc_factors, validate_goose_len, write_xpm_config)

logger = logging.getLogger(__name__)

def read_config(config_file):
    """
    Read in the config file for the screen.
    """
    with open(config_file, "r") as f:
        conf = yaml.safe_load(f)
    return conf

class NCMetadataDisplay(Display):
    """
    Class for copper linac xray metatdata user display.
    """
    def __init__(
        self,
        parent=QtWidgets.QWidget,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

    def setup_display(self, config):
        """
        Run the things we would run during init but can't because I can't
        figure out how to pass variables to sub-displays at init....
        """
        self._config = read_config(config)
        if self._config is None:
            raise ValueError(f"Could not read config file {config}")

        logger.info(f"Read configuration file: {config}")
        logger.debug(f"Configuration sections: {self._config.keys()}")
        logger.debug(f"{self._config}")

        self.update_pvs()

    def update_pvs(self):
        """
        Modify RBV widgets to use the PV(s) specified in the config file.
        """
        #  metadata
        nc_base = self._config['main']['nc_meta_pv']

        logger.debug(f"NC metadata base PV: {nc_base}")

        self.rate_rbv.set_channel(f"ca://{nc_base}:LCLSBEAMRATE")
        self.hard_rate_rbv.set_channel(f"ca://{nc_base}:NC_HARDRATE")
        self.soft_rate_rbv.set_channel(f"ca://{nc_base}:NC_SOFTRATE")

        # self.pattern_name_rbv.set_channel(f"ca://{nc_base}:NAME")

    def ui_filename(self):
        return "nc_metadata.ui"

    def ui_filepath(self):
        return path.join(
            path.dirname(path.realpath(__file__)), self.ui_filename()
        )


class SCMetadataDisplay(Display):
    """
    Class for SC metatdata user display.
    """
    def __init__(
        self,
        parent=QtWidgets.QWidget,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

    def setup_display(self, config):
        """
        Run the things we would run during init but can't because I can't
        figure out how to pass variables to sub-displays at init....
        """
        self._config = read_config(config)
        if self._config is None:
            raise ValueError(f"Could not read config file {config}")

        logger.info(f"Read configuration file: {config}")
        logger.debug(f"Configuration sections: {self._config.keys()}")
        logger.debug(f"{self._config}")

        self.update_pvs()

    def update_pvs(self):
        """
        Modify RBV widgets to use the PV(s) specified in the config file.
        """
        # SC metadata
        sc_base = self._config['main']['sc_meta_pv']

        logger.debug(f"SC metadata base PV: {sc_base}")

        self.pattern_name_rbv.set_channel(f"ca://{sc_base}:NAME")
        self.rate_rbv.set_channel(f"ca://{sc_base}:RATE_RBV")
        self.time_source_rbv.set_channel(f"ca://{sc_base}:TIME_SRC")
        self.offset_rbv.set_channel(f"ca://{sc_base}:OFFSET_RBV")
        self.time_slot_rbv.set_channel(f"ca://{sc_base}:TS")
        self.time_slot_mask_rbv.set_channel(f"ca://{sc_base}:TSMASK")

    def ui_filename(self):
        return "sc_metadata.ui"

    def ui_filepath(self):
        return path.join(
            path.dirname(path.realpath(__file__)), self.ui_filename()
        )


class LaserConfigDisplay(Display):
    """
    Class for rep. rate configuration application user display.
    """
    # Laser configuration widgets
    on_time_ec_rbv: pydm_widgets.PyDMLabel
    on_time_rate_rbv: pydm_widgets.PyDMLabel
    off_time_ec_rbv: pydm_widgets.PyDMLabel
    off_time_rate_rbv: pydm_widgets.PyDMLabel
    all_shots_ec_rbv: pydm_widgets.PyDMLabel
    all_shots_rate_rbv: pydm_widgets.PyDMLabel

    start_timeslot_inputs: QtWidgets.QWidget
    nc_timeslot_selector: QtWidgets.QComboBox

    start_bucket_inputs_sc: QtWidgets.QWidget
    sc_bucket_control_box: QtWidgets.QComboBox
    sc_bucket_edit: QtWidgets.QLineEdit
    sc_bucket_rbv: pydm_widgets.PyDMLabel
    nc_bucket_rbv: pydm_widgets.PyDMLabel
    sc_bucket_is_synced: pydm_widgets.PyDMByteIndicator
    sc_bucket_is_synced_label: pydm_widgets.PyDMLabel

    start_bucket_inputs_nc: QtWidgets.QWidget
    nc_bucket_edit: QtWidgets.QLineEdit

    timestamp_rbv: pydm_widgets.PyDMLabel

    total_rate_box: QtWidgets.QComboBox
    total_rate_label: QtWidgets.QLabel
    goose_rate_box: QtWidgets.QComboBox
    goose_rate_label: QtWidgets.QLabel
    goose_effective_rate_label: QtWidgets.QLabel
    goose_arrival_box: QtWidgets.QComboBox
    goose_arrival_label: QtWidgets.QLabel
    goose_start_label: QtWidgets.QLabel
    goose_start_input: QtWidgets.QLineEdit
    goose_len_label: QtWidgets.QLabel
    goose_len_input: QtWidgets.QLineEdit


    apply_button: pydm_widgets.PyDMPushButton
    status_label: QtWidgets.QLabel

    def __init__(
        self,
        parent=QtWidgets.QWidget,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

    def setup_display(self, config):
        """
        Run the things we would run during init but can't because I can't
        figure out how to pass variables to sub-displays at init....
        """
        self._config = read_config(config)
        if self._config is None:
            raise ValueError(f"Could not read config file {config}")

        # Event code data
        self._engine1 = int(self._config['main']['engine1'])
        self._engine2 = int(self._config['main']['engine2'])

        logger.info(f"Read configuration file: {config}")
        logger.debug(f"Configuration sections: {self._config.keys()}")
        logger.debug(f"{self._config}")

        self.status_label.setText("Status: Idle")
        # Hiding this because the status doesn't work well without threading
        # the configuration method. Will remove once that's done in a later PR
        self.status_label.setVisible(False)

        self.update_pvs()

        self._base_rates: list = make_possible_rates(nc_factors)
        self.update_base_rates(False)

        self.update_goose_rates()
        self.update_goose_arrival()

        self.update_goose_vis()

        self.update_bucket_control_items()
        self.update_bucket_control_vis()

        self.total_rate_box.currentTextChanged.connect(self.update_goose_rates)

        self.goose_arrival_box.currentTextChanged.connect(
            self.update_goose_vis
        )

        self.sc_bucket_control_box.currentTextChanged.connect(
            self.update_bucket_control_vis
        )

        self.goose_len_input.editingFinished.connect(self._validate_goose_len)


    def update_pvs(self):
        """
        Modify RBV widgets to use the PV(s) specified in the config file.
        """
        # Event code data
        xpm_pv = self._config['main'].get('xpm_pv', "NA")
        on_time_idx = self._engine1 * 4
        off_time_idx = (self._engine1 * 4) + 1
        all_shots_idx = (self._engine1 * 4) + 2
        self._on_time = 256 + on_time_idx
        self._off_time = 256 + off_time_idx
        self._all_shots = 256 + all_shots_idx

        self.on_time_ec_rbv.setText(str(self._on_time))
        self.off_time_ec_rbv.setText(str(self._off_time))
        self.all_shots_ec_rbv.setText(str(self._all_shots))
        self.on_time_rate_rbv.set_channel(
            f"pva://{xpm_pv}:SEQCODES/Rate/{on_time_idx}"
        )
        self.off_time_rate_rbv.set_channel(
            f"pva://{xpm_pv}:SEQCODES/Rate/{off_time_idx}"
        )
        self.all_shots_rate_rbv.set_channel(
            f"pva://{xpm_pv}:SEQCODES/Rate/{all_shots_idx}"
        )

        # "Notepad" PVs
        notepad_pv = self._config['main']['notepad_pv']
        self.sc_bucket_rbv.set_channel(f"ca://{notepad_pv}:SC_BUCKET")
        self.nc_bucket_rbv.set_channel(f"ca://{notepad_pv}:SC_BUCKET")
        self.timestamp_rbv.set_channel(f"ca://{notepad_pv}:SC_TIMESTAMP")

        # start buckets synced indicator
        sc_base = self._config['main']['sc_meta_pv']
        self.sc_bucket_is_synced.set_channel(
            f"calc://compare_buckets?"
            f"laser_bucket=ca://{notepad_pv}:SC_BUCKET&"
            f"xray_bucket=ca://{sc_base}:OFFSET_RBV&"
            f"expr=1 if laser_bucket==xray_bucket else 0"
        )
        self.sc_bucket_is_synced_label.rules = '''[
        {
            "name": "bool_label",
            "property": "Text",
            "initial_value": "",
            "expression": "{0: \\"Not-Synced\\" , 1: \\"    Synced\\"}[ch[0]]",
            "channels": [
            {
                "channel": "calc://compare_buckets",
                "trigger": true,
                "use_enum": false
            }
            ],
            "notes": ""
        }
        ]'''

        logger.debug(f"Engine 1: {self._engine1}")
        logger.debug(f"Engine 2: {self._engine2}")
        logger.debug(f"On time EC: {self._on_time}")
        logger.debug(f"Off time EC: {self._off_time}")
        logger.debug(f"On time index: {on_time_idx}")
        logger.debug(f"Off time index: {off_time_idx}")

    def ui_filename(self):
        return "rep_rate_config.ui"

    def ui_filepath(self):
        return path.join(
            path.dirname(path.realpath(__file__)), self.ui_filename()
        )

    def update_base_rates(self, is_superconducting):
        if is_superconducting:
            factors = sc_factors
            self._clock_rate = 910000
        else:
            factors = nc_factors
            self._clock_rate = 120

        self._base_rates = make_possible_rates(factors)
        # Restrict allowed rates to > 1kHz for sc and >5hz for NC, but keep all rates in
        # self._base_rates for allowed goose rate calculation
        if is_superconducting:
            rate_limit = 300
        else:
            rate_limit = 5
        for rate in self._base_rates:
            # TODO: The calculation of goose rates could probably be
            # decoupled from the base rate array.
            if rate <rate_limit:
                continue
            self.total_rate_box.addItem(str(rate))

        # always select the highest rate when switching menus
        self.total_rate_box.setCurrentIndex(self.total_rate_box.count() - 1)

        logger.debug(f"Allowed base rates: {self._base_rates}")

    @property
    def base_rate(self):
        text_selection = self.total_rate_box.currentText()
        if text_selection == "":
            #needed when switching between NC and SC
            return None
        return int(text_selection)

    def update_goose_vis(self):
        """
        Update visibility of goose rate control widget based on goose mode
        status.
        """
        self.goose_rate_box.setVisible(self.goose_enabled)
        self.goose_rate_label.setVisible(self.goose_enabled)
        self.goose_len_label.setVisible(self.goose_enabled)
        self.goose_len_input.setVisible(self.goose_enabled)
        self.goose_start_label.setVisible(self.goose_enabled)
        self.goose_start_input.setVisible(self.goose_enabled)

    def update_goose_rates(self):
        if self._base_rates is not None and self.base_rate is not None:
            goose_rates = allowed_goose_rates(
                self.base_rate,
                self._base_rates
            )
            self.goose_rate_box.clear()
            self.goose_len_input.setText("1")
            self.goose_start_input.setText("1")
            for rate in goose_rates:
                self.goose_rate_box.addItem(str(rate))
            logger.debug(f"Requested base rate: {rate}")
            logger.debug(f"Allowed goose rates: {goose_rates}")

    @property
    def goose_rate(self):
        return int(self.goose_rate_box.currentText())

    def update_goose_arrival(self):
        cfgs = self._config.get('goose_arrival_configs', None)
        if cfgs is None:
            return
        if cfgs is not None:
            logger.debug(f"Goose arrival configs: {cfgs}")
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

    def update_bucket_control_items(self):
        modes = ['Manual', 'Auto']
        for mode in modes:
            self.sc_bucket_control_box.addItem(mode)

    @property
    def start_ts1(self) -> bool:
        """  Starts on TS1 if True, TS4 if False"""
        return self.nc_timeslot_selector.currentIndex() == 0

    @property
    def bucket_control_enabled(self):
        txt = self.sc_bucket_control_box.currentText()
        if txt != "Auto":
            return True
        else:
            return False

    def update_bucket_control_vis(self):
        self.sc_bucket_edit.setVisible(self.bucket_control_enabled)

    @property
    def sc_manual_bucket(self):
        return int(self.sc_bucket_edit.text())

    @property
    def nc_manual_bucket(self):
        return int(self.nc_bucket_edit.text())

    def _validate_goose_len(self):
        """Clamp goose_len_input to valid range via validate_goose_len."""
        if self.base_rate is None or not self.goose_enabled:
            return
        try:
            goose_len = int(self.goose_len_input.text())
        except ValueError:
            logger.warning(f"invalid goose len {self.goose_len_input.text()}, reverted to 1")
            goose_len = 1
        base_div = self._clock_rate // self.base_rate
        goose_div = self._clock_rate // self.goose_rate
        valid = validate_goose_len(base_div, goose_div, goose_len)
        self.goose_len_input.setText(str(valid))


class ExpertDisplay(Display):
    """
    Class for expert level user display.
    """
    xpm_table: pydm_widgets.PyDMNTTable
    tpr_frame: QtWidgets.QFrame
    rbv_frame: QtWidgets.QFrame

    def __init__(
        self,
        parent=None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

    def ui_filename(self):
        return "expert_screen.ui"

    def ui_filepath(self):
        return path.join(
            path.dirname(path.realpath(__file__)), self.ui_filename()
        )

    def setup_display(self, config):

        self._config = read_config(config)
        if self._config is None:
            raise ValueError(f"Could not read config file {config}")

        happi_db_path = self._config['main'].get('laser_database',None)
        if happi_db_path is not None:
            self._db = happi.Client(
                path=happi_db_path
            )
        else:
            self._db = None

        xpm_pv = self._config['main'].get('xpm_pv', "NA")
        self.xpm_table.set_channel(f"pva://{xpm_pv}:SEQCODES")

        self.configure_rbv_frames()

    def set_visibility(self, visible):
        """
        Update visibility of "expert mode" widgets based on expert mode check
        box status.
        """
        self.xpm_table.setVisible(visible)
        self.tpr_frame.setVisible(visible)
        self.rbv_frame.setVisible(visible)

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


class UserConfigDisplay(Display):
    """
    Class for rep. rate configuration application user display.
    """

    # Top level widgets
    screen_title: pydm_widgets.PyDMLabel
    nc_sc_selection: QtWidgets.QComboBox

    # SC Metadata
    sc_metadata_widget: SCMetadataDisplay

    # NC Metadata
    nc_metadata_widget: NCMetadataDisplay

    # Laser Config
    laser_config_widget: LaserConfigDisplay

    # Expert mode widgets
    expert_display_widget: ExpertDisplay
    expert_checkbox: QtWidgets.QCheckBox

    def __init__(
        self,
        parent=None,
        config: str = "",
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.laser_config_widget.setup_display(config)

        self.sc_metadata_widget.setup_display(config)

        self.nc_metadata_widget.setup_display(config)

        self.expert_display_widget.setup_display(config)

        self._config = read_config(config)
        if self._config is None:
            raise ValueError(f"Could not read config file {config}")

        if self._config is not None:
            db_path = self._config.get('main', {}).get('laser_database')
            if db_path is None:
                self._db = None
            else:
                self._db = happi.Client(path=db_path)

        self._engine1 = int(self._config['main']['engine1'])
        self._engine2 = int(self._config['main']['engine2'])

        self.screen_title.setText(self._config['main']['title'])

        self.update_expert_vis()

        self.update_sc_nc()

        self.laser_config_widget.apply_button.clicked.connect(
            self.apply_config
        )
        self.expert_checkbox.stateChanged.connect(self.update_expert_vis)

        self.nc_sc_selection.currentIndexChanged.connect(
            self.update_sc_nc
        )

    def ui_filename(self):
        return "user_config.ui"

    def ui_filepath(self):
        return path.join(
            path.dirname(path.realpath(__file__)), self.ui_filename()
        )

    def update_expert_vis(self):
        self.expert_display_widget.set_visibility(self.expert_mode)


    def update_sc_nc(self):
        """
        Resets widgets based on user selections of Linac type (NC or SC).
        """
        # first clear previous rates
        self._base_rates = None
        self.laser_config_widget.total_rate_box.clear()

        #then re_init them
        self.laser_config_widget.update_base_rates(self.is_superconducting)
        # always reset goose config selection
        # self.laser_config_widget.goose_arrival_box.setCurrentIndex(0)

        # update visibilities of key widgets
        if self.is_superconducting:
            self.sc_metadata_widget.show()
            self.nc_metadata_widget.hide()
            self.laser_config_widget.start_timeslot_inputs.hide()
            self.laser_config_widget.start_bucket_inputs_sc.show()
            self.laser_config_widget.start_bucket_inputs_nc.hide()
        else:
            self.sc_metadata_widget.hide()
            self.nc_metadata_widget.show()
            self.laser_config_widget.start_timeslot_inputs.show()
            self.laser_config_widget.start_bucket_inputs_sc.hide()
            self.laser_config_widget.start_bucket_inputs_nc.show()


    @property
    def expert_mode(self):
        return self.expert_checkbox.isChecked()

    @property
    def is_superconducting(self):
        return self.nc_sc_selection.currentIndex() == 1

    @property
    def offset(self):
        """
        Return the SC bucket offset to be used in pattern generation.
        """
        if self.is_superconducting:
            # Use manual SC bucket if enabled
            if self.laser_config_widget.bucket_control_enabled:
                val = self.laser_config_widget.nc_manual_bucket
            # Otherwise try to detect offset from AD PVs
            else:
                # This is a float PV for some reason
                val = int(self.sc_metadata_widget.offset_rbv.value)
        else:
            val = self.laser_config_widget.nc_manual_bucket

        return val

    def write_offset(self, value):
        """
        Write the given value into the offset PV for this system.
        """
        pv = self._config['main']['notepad_pv'] + ':SC_BUCKET'
        sig = EpicsSignal(pv)
        sig.put(value)

    def write_timestamp(self):
        """
        Write the current time into the timestamp PV for this system.
        """
        pv = self._config['main']['notepad_pv'] + ':SC_TIMESTAMP'
        sig = EpicsSignal(pv)
        t = time.asctime()
        sig.put(t)

    def apply_device_config(self):
        if self._db is None:
            #no devices need configuration
            return
        supported_devices = [
            "pcdsdevices.tpr.TprTrigger",
            "ophyd.signal.EpicsSignal",
        ]
        for devclass in supported_devices:
            devices = self._db.search(device_class=devclass)
            for device in devices:
                name = device.metadata['name']
                if name == "TIC_Averaging":  # Handle this as special case
                    navg = self.calc_tic_averaging(
                        self.laser_config_widget.base_rate
                    )
                    instance = device.get()
                    instance.put(navg)
                elif name in self.laser_config_widget.arrival_config:
                    instance = device.get()
                    config = self.laser_config_widget.arrival_config[name]
                    if devclass == "ophyd.signal.EpicsSignal":
                        if 'val' in config.keys():
                            instance.put(config['val'])
                            logger.info(f"Put {device} {config['val']}")
                        else:
                            raise Exception("Missing 'val' for EpicsSignal")
                    else:
                        instance.configure(config)
                        logger.info(f"Configure {device} {config}")

    def calc_tic_averaging(self, total_rate):
        """
        Calculate the best TIC averaging setting based on total rate. The
        goal is to have about 50ms of data in the TIC measurement. The allowed
        averaging settings on the TIC follow a 1-2-5 scale, approximating a
        logarithm.
        """
        rate = int(total_rate)
        sample_size = 200 if rate > 2000 else 100
        return sample_size

    def apply_laser_rates(self):
        """
        Generate and apply the XPM configuration for the laser on/off time
        event codes.
        """
        try:
            goose_len = int(self.laser_config_widget.goose_len_input.text())
        except ValueError:
            goose_len = 1
        try:
            goose_start = int(self.laser_config_widget.goose_start_input.text())
        except ValueError:
            goose_start = 1

        goose_rate = (
            self.laser_config_widget.goose_rate
            if self.laser_config_widget.goose_enabled
            else None
        )

        seqdesc, instrset = build_laser_sequence(
            is_sc=self.is_superconducting,
            base_rate=self.laser_config_widget.base_rate,
            goose_rate=goose_rate,
            goose_enabled=self.laser_config_widget.goose_enabled,
            offset=self.offset,
            start_ts1=self.laser_config_widget.start_ts1,
            goose_len=goose_len,
            goose_start=goose_start,
            bay=self._config['main']['bay'],
        )

        xpm_pv = self._config['main'].get('xpm_pv', None)
        if xpm_pv is not None:
            write_xpm_config(xpm_pv, self._engine1, seqdesc, instrset)

    def apply_base_rates(self):
        """
        Generate and apply the XPM configuration for the "base" laser rates
        that should always be available.
        """
        logger.info("Applying base rates")
        logger.info(f"Offset: {self.offset}")

        seqdesc, instrset = build_base_sequence(
            is_sc=self.is_superconducting,
            offset=self.offset,
            bay=self._config['main']['bay'],
        )

        xpm_pv = self._config['main'].get('xpm_pv', None)
        if xpm_pv is not None:
            write_xpm_config(xpm_pv, self._engine2, seqdesc, instrset)

    def set_tic_enable(self, enable):
        """
        Function to help with enabling/disabling the TIC gate trigger. This
        prevents the TIC measurement from getting messed up during
        configuration.
        """
        if self._db is None:
            return
        if enable:
            conf = {'enable_trg_cmd': 'Enabled', 'enable_ch_cmd': 'Enabled'}
        else:
            conf = {'enable_trg_cmd': 'Disabled', 'enable_ch_cmd': 'Disabled'}

        trig_names = ['TIC_Gate', 'TIC_Gate_Goose']
        devices = self._db.search(device_class="pcdsdevices.tpr.TprTrigger")
        for device in devices:
            name = device.metadata['name']
            if name in trig_names:
                instance = device.get()
                instance.configure(conf)

    def update_status(self, status):
        self.laser_config_widget.status_label.setText(status)

    def apply_config(self):
        """
        Apply the requested configuration to the system.
        """
        self.update_status("Status: Configuring...")
        self.set_tic_enable(False)
        self.apply_base_rates()
        self.apply_laser_rates()
        self.apply_device_config()
        self.set_tic_enable(True)
        self.write_offset(self.offset)
        self.write_timestamp()
        self.update_status("Status: Config Done")
