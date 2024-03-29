from functools import partial

import yaml
from ophyd import EpicsSignal
from pydm import Display
from pydm.widgets import PyDMDrawingLine, PyDMLabel, PyDMPushButton
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QGridLayout, QSizePolicy, QSpacerItem


class App(Display):
    def __init__(self, parent=None, args=None, macros=None):
        # print(f'args={args}, macros={macros}')

        # Read in config file
        # TODO add argparse, make this an arg
        cfg_file = "opcpa_tpr_config/neh_config.yaml"

        config = {}
        with open(cfg_file, "r") as f:
            config = yaml.safe_load(f)
        self.config = config

        print(f"Loaded config {cfg_file}")
        # print(config)

        # Call super after handling args/macros but before doing pyqt stuff
        super().__init__(parent=parent, args=args, macros=macros)

        # Now it is safe to refer to self.ui and access your widget objects
        # It is too late to do any macros processing

        # Setup main areas of GUI
        self.setup_main()

        # Setup laser specific portions of GUI
        for laser in self.config["lasers"]:
            self.setup_rbvs(laser)
            self.setup_configs(laser)

    def ui_filename(self):
        return "opcpa_tpr_config.ui"

    def setup_main(self):
        """
        Setup the central widgets for the screen.
        """
        self.ui.screen_title.setText(self.config["main"]["title"])
        xpm_pv = self.config["main"]["xpm_pv"]
        self.ui.xpm_label.setText(xpm_pv)
        self.ui.xpm.set_channel(f"pva://{xpm_pv}")

    def setup_rbvs(self, laser):
        """
        Setup the RBV widgets for the given laser system.

        Arguments
        ---------
        laser: The key name of the laser to be used.
        """
        vlayout = self.ui.lasers_vlayout
        grid = QGridLayout()

        las_conf = self.config["lasers"][laser]

        # Add description widgets
        desc_font = QFont()
        desc_font.setBold(True)
        desc_font.setUnderline(True)
        laser_desc = PyDMLabel()
        laser_desc.setText(las_conf["laser_desc"])
        laser_desc.setFont(desc_font)
        vlayout.addWidget(laser_desc)

        # Setup column headers
        desc = PyDMLabel()
        desc.setText("Trigger")
        grid.addWidget(desc, 0, 0)
        reprate = PyDMLabel()
        reprate.setText("Rep. Rate")
        grid.addWidget(reprate, 0, 1)
        ratemode = PyDMLabel()
        ratemode.setText("Rate Mode")
        grid.addWidget(ratemode, 0, 2)
        eventcode = PyDMLabel()
        eventcode.setText("Event Code")
        grid.addWidget(eventcode, 0, 3)
        width = PyDMLabel()
        width.setText("Width (ns)")
        grid.addWidget(width, 0, 4)
        delay = PyDMLabel()
        delay.setText("Delay (ns)")
        grid.addWidget(delay, 0, 5)

        # Setup PV RBVs
        tpr_base = las_conf["tpr_base"]
        labels = ["DESC", "RATE", "RATEMODE", "SEQCODE", "SYS2_TWID",
                  "SYS2_TDES"]
        for nchannel, channel in enumerate(las_conf["channels"], start=1):
            for nlabel, label in enumerate(labels):
                child = PyDMLabel()
                if label == "DESC":
                    val = las_conf["channels"][f"{channel}"]["desc"]
                    child.setText(val)
                elif label in ["SYS2_TWID", "SYS2_TDES"]:
                    # These need TRG instead of CH
                    tpr_ch = las_conf["channels"][f"{channel}"]["ch"]
                    pv = f"ca://{tpr_base}:TRG{tpr_ch}_{label}"
                    child.set_channel(pv)
                else:
                    tpr_ch = las_conf["channels"][f"{channel}"]["ch"]
                    pv = f"ca://{tpr_base}:CH{tpr_ch}_{label}"
                    child.set_channel(pv)
                grid.addWidget(child, nchannel, nlabel)
        # Add to GUI
        vlayout.addLayout(grid)

    def setup_configs(self, laser):
        """
        Setup the configuration buttons for the given laser system.

        Arguments
        ---------
        laser: The name of the laser configuration to be used.
        """
        vlayout = self.ui.lasers_vlayout
        grid = QGridLayout()

        config_desc = PyDMLabel()
        config_font = QFont()
        config_font.setUnderline(True)
        config_desc.setText("Set Rep. Rate Configuration")
        config_desc.setFont(config_font)
        vlayout.addWidget(config_desc)

        las = self.config["lasers"][laser]
        for ncfg, cfg in enumerate(las["rate_configs"]):
            button = PyDMPushButton(f"{laser}_{cfg}")
            rate = las["rate_configs"][cfg]["rate"]
            button.setText(f"{rate}")
            button.showConfirmDialog = True
            row, col = divmod(ncfg, 4)
            row += 1  # Leave first row for title
            grid.addWidget(button, row, col)
            button.clicked.connect(
                partial(self.set_configuration, las, cfg)
            )
        vlayout.addLayout(grid)

        # Finish the section
        line = PyDMDrawingLine()
        vlayout.addWidget(line)

        space = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vlayout.addItem(space)

    def set_configuration(self, laser, config):
        """
        Apply the given configuration to the TPR.

        Arguments
        ---------
        laser: The name of the laser configuration to be used.

        config: The rep rate configuration to be applied when calling this
                function.
        """
        tpr_base = laser["tpr_base"]
        rate_conf = laser["rate_configs"][config]
        for channel in laser["channels"]:
            if channel in laser["rate_configs"][config]:
                tpr_ch = laser["channels"][f"{channel}"]["ch"]
                # Set rate mode
                ratemode_val = rate_conf[channel]["ratemode"]
                ratemode_sig = EpicsSignal(f"{tpr_base}:CH{tpr_ch}_RATEMODE")
                ratemode_sig.put(ratemode_val)
                # Set rate
                rate_val = rate_conf[channel]["rate"]
                if ratemode_val == "Fixed":
                    rate_sig = EpicsSignal(f"{tpr_base}:CH{tpr_ch}_FIXEDRATE")
                    rate_sig.put(rate_val)
                elif ratemode_val == "Seq":
                    rate_sig = EpicsSignal(f"{tpr_base}:CH{tpr_ch}_SEQCODE")
                    event_code = laser["rep_rates"][rate_val]
                    rate_sig.put(event_code)
                else:
                    raise ValueError(f"Unknown ratemode {ratemode_val}")
                # Enable/Disable the trigger
                enable_val = rate_conf[channel]["enable"]
                trg_sig = EpicsSignal(f"{tpr_base}:TRG{tpr_ch}_SYS2_TCTL")
                trg_sig.put(enable_val)
                ch_sig = EpicsSignal(f"{tpr_base}:CH{tpr_ch}_SYS2_TCTL")
                ch_sig.put(enable_val)
