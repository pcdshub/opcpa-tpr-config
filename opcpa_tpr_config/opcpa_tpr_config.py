# from functools import partial

import yaml
# from pcdsdevices.tpr import TimingMode, TprTrigger
from pydm import Display
from pydm.widgets import PyDMDrawingLine, PyDMLabel, PyDMPushButton
from qtpy.QtGui import QFont
from qtpy.QtWidgets import QComboBox, QGridLayout, QSizePolicy, QSpacerItem


class App(Display):
    def __init__(self, parent=None, args=None, macros=None):
        print(f'args={args}, macros={macros}')

        cfg_file = args[0]

        config = {}
        with open(cfg_file, "r") as f:
            config = yaml.safe_load(f)
        self.config = config

        print(f"Loaded config {cfg_file}")

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

        op = PyDMLabel()
        op.setText("Logic")
        grid.addWidget(op, 0, 6)

        enabled = PyDMLabel()
        enabled.setText("Status")
        grid.addWidget(enabled, 0, 7)

        # Setup PV RBVs
        labels = ["DESC", "RATE", "RATEMODE", "SEQCODE", "SYS2_TWID",
                  "SYS2_TDES", "TCMPL", "SYS2_TCTL"]

        nchannel = 1
        for channel in las_conf["channels"]:
            if las_conf["channels"][channel]["show"]:
                for nlabel, label in enumerate(labels):
                    child = self.configure_ch_rbv_widget(laser, label, channel)
                    grid.addWidget(child, nchannel, nlabel)
                nchannel += 1
        # Add to GUI
        vlayout.addLayout(grid)

    def configure_ch_rbv_widget(self, laser, label, channel):
        """
        Setup a channel RBV widget.

        returns:
            PyDMLabel
        """
        las_conf = self.config["lasers"][laser]
        tpr_base = self.config["lasers"][laser]["tpr_base"]
        child = PyDMLabel()
        if label == "DESC":
            val = las_conf["channels"][f"{channel}"]["desc"]
            child.setText(val)
        elif label in ["SYS2_TWID", "SYS2_TDES", "TCMPL", "SYS2_TCTL"]:
            # These need TRG instead of CH
            tpr_ch = las_conf["channels"][f"{channel}"]["ch"]
            pv = f"ca://{tpr_base}:TRG{tpr_ch}_{label}"
            child.set_channel(pv)
        else:
            tpr_ch = las_conf["channels"][f"{channel}"]["ch"]
            pv = f"ca://{tpr_base}:CH{tpr_ch}_{label}"
            child.set_channel(pv)
        return child

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

        las = self.config['lasers'][laser]

        cfg_sections = ['laser_rate_configs', 'goose_rate_configs',
                        'goose_arrival_configs']

        cfgd = dict()  # Dict to store widgets for later use

        for nsection, section in enumerate(cfg_sections):
            desc = PyDMLabel()
            desc.setText(las[section]['desc'])
            grid.addWidget(desc, 0, nsection)

            cbox = QComboBox()
            cfgs = las[section]
            cfgs.pop('desc', None)  # Remove description field before loop

            for ncfg, cfg in enumerate(cfgs):
                txt = las[section][cfg]['desc']
                data = las[section][cfg]
                cbox.insertItem(ncfg, txt, userData=data)
            grid.addWidget(cbox, 1, nsection)

            cfgd[section] = cbox

        apply_button = PyDMPushButton("Apply")
        apply_button.clicked.connect(
            lambda: self.apply_configuration(
                las,
                cfgd['laser_rate_configs'],
                cfgd['goose_rate_configs'],
                cfgd['goose_arrival_configs']
            )
        )
        grid.addWidget(apply_button, 1, nsection+1)
        # Setup goose rate configs
#        las = self.config["lasers"][laser]
#        for ncfg, cfg in enumerate(las["rate_configs"]):
#            button = PyDMPushButton(f"{laser}_{cfg}")
#            rate = las["rate_configs"][cfg]["rate"]
#            button.setText(f"{rate}")
#            button.showConfirmDialog = True
#            row, col = divmod(ncfg, 4)
#            row += 1  # Leave first row for title
#            grid.addWidget(button, row, col)
#            button.clicked.connect(
#                partial(self.set_configuration, las, cfg)
#            )
        vlayout.addLayout(grid)

        # Finish the section
        line = PyDMDrawingLine()
        vlayout.addWidget(line)

        space = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vlayout.addItem(space)

    def apply_configuration(self, laser, base, goose, arrival):

        self.set_tpr_configuration(laser, base)
        # self.set_goose_configuration(laser, goose)
        # self.set_arrival_configuration(laser, arrival)

    def set_tpr_configuration(self, laser, cbox):
        """
        Apply the given configuration to the TPR.

        Arguments
        ---------
        laser: The name of the laser configuration to be used.

        config: The rep rate configuration to be applied when calling this
                function.
        """
#        tpr_base = laser["tpr_base"]
        print(f"index {cbox.currentIndex()}")
        print(f"text {cbox.currentText()}")
        print(f"userdata: {cbox.currentData()}")
#        rate_conf = laser["laser_rate_configs"][config]
#        for channel in laser["channels"]:
#            if channel in laser["rate_configs"][config]:
#                tpr_ch = int(laser["channels"][f"{channel}"]["ch"])
#                tpr = TprTrigger(tpr_base, channel=tpr_ch,
#                                 timing_mode=TimingMode.LCLS2,
#                                 name=f"ch{tpr_ch}")
#                tpr.wait_for_connection()  # pvs connect slow for some reason
#                tpr.configure(rate_conf[channel])

    def set_arrival_configuration(self, laser, config):
        print(config)

    def set_goose_configuration(self, laser, config):
        print(config)
