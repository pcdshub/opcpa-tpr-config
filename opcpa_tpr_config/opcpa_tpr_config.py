# from functools import partial

import yaml
from happi import Client
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

        # Setup some common properties
        title_font = QFont()
        title_font.setBold(True)
        title_font.setUnderline(True)
        self.title_font = title_font

        header_font = QFont()
        header_font.setUnderline(True)
        self.header_font = header_font

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
        las_db = Client(path=las_conf['laser_database'])

        # Add description widgets
        laser_desc = PyDMLabel()
        laser_desc.setText(las_conf["laser_desc"])
        laser_desc.setFont(self.title_font)
        vlayout.addWidget(laser_desc)

        # Setup TPR triggers first
        grid = self.setup_tpr_rbvs(las_conf, las_db, grid)

        # Add to GUI
        vlayout.addLayout(grid)

        # Setup EpicsSignals
        grid = QGridLayout()  # Setup new grid
        grid = self.setup_signal_rbvs(las_conf, las_db, grid)

        # Add to GUI
        vlayout.addLayout(grid)

    def setup_tpr_rbvs(self, las_conf, las_db, grid):
        """
        Setup RBV widgets for TPR triggers associated with the laser system.
        """
        # Setup column headers
        desc = PyDMLabel()
        desc.setText("Trigger")
        desc.setFont(self.header_font)
        grid.addWidget(desc, 0, 0)

        reprate = PyDMLabel()
        reprate.setText("Rep. Rate")
        reprate.setFont(self.header_font)
        grid.addWidget(reprate, 0, 1)

        ratemode = PyDMLabel()
        ratemode.setText("Rate Mode")
        ratemode.setFont(self.header_font)
        grid.addWidget(ratemode, 0, 2)

        eventcode = PyDMLabel()
        eventcode.setText("Event Code")
        eventcode.setFont(self.header_font)
        grid.addWidget(eventcode, 0, 3)

        width = PyDMLabel()
        width.setText("Width (ns)")
        width.setFont(self.header_font)
        grid.addWidget(width, 0, 4)

        delay = PyDMLabel()
        delay.setText("Delay (ns)")
        delay.setFont(self.header_font)
        grid.addWidget(delay, 0, 5)

        op = PyDMLabel()
        op.setText("Logic")
        op.setFont(self.header_font)
        grid.addWidget(op, 0, 6)

        enabled = PyDMLabel()
        enabled.setText("Status")
        enabled.setFont(self.header_font)
        grid.addWidget(enabled, 0, 7)

        # Setup TPR PV RBVs
        tpr_trigs = las_db.search(device_class='pcdsdevices.tpr.TprTrigger')
        ntrig = 1
        for trig in tpr_trigs:
            if trig.metadata['active']:
                name = trig.metadata['name']
                trig_conf = las_conf['devices'][name]
                rbvs = trig_conf['rbvs']
                for nrbv, rbv in enumerate(rbvs):
                    child = self.configure_rbv_widget(trig, rbv)
                    grid.addWidget(child, ntrig, nrbv)
                ntrig += 1

        return grid

    def setup_signal_rbvs(self, las_conf, las_db, grid):
        """
        Setup RBV widgets for TPR triggers associated with the laser system.
        """
        # Setup column headers
        desc = PyDMLabel()
        desc.setText("Signal")
        desc.setFont(self.header_font)
        grid.addWidget(desc, 0, 0)

        val = PyDMLabel()
        val.setText("Value")
        val.setFont(self.header_font)
        grid.addWidget(val, 0, 1)

        # Setup Signal PV RBVs
        signals = las_db.search(device_class='ophyd.signal.EpicsSignal')
        nsig = 1
        for signal in signals:
            if signal.metadata['active']:
                name = signal.metadata['name']
                sig_conf = las_conf['devices'][name]
                rbvs = sig_conf['rbvs']
                for nrbv, rbv in enumerate(rbvs):
                    child = self.configure_rbv_widget(signal, rbv)
                    grid.addWidget(child, nsig, nrbv)
                nsig += 1

        space = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        grid.addItem(space, nsig, nrbv+1)

        return grid

    def configure_rbv_widget(self, dev, rbv):
        """
        Setup a ophyd device RBV widget.

        returns:
            PyDMLabel
        """
        child = PyDMLabel()
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

    def setup_configs(self, laser):
        """
        Setup the configuration buttons for the given laser system.

        Arguments
        ---------
        laser: The name of the laser configuration to be used.
        """

        las_conf = self.config["lasers"][laser]
        las_db = Client(path=las_conf['laser_database'])

        vlayout = self.ui.lasers_vlayout
        grid = QGridLayout()

        config_desc = PyDMLabel()
        config_desc.setText("Set Rep. Rate Configuration")
        config_desc.setFont(self.header_font)
        vlayout.addWidget(config_desc)

        cfg_sections = ['laser_rate_configs', 'goose_rate_configs',
                        'goose_arrival_configs']

        cfgd = dict()  # Dict to store widgets for later use

        for nsection, section in enumerate(cfg_sections):
            desc = PyDMLabel()
            desc.setText(las_conf[section]['desc'])
            grid.addWidget(desc, 0, nsection)

            cbox = QComboBox()
            cfgs = las_conf[section]
            cfgs.pop('desc', None)  # Remove description field before loop

            for ncfg, cfg in enumerate(cfgs):
                txt = las_conf[section][cfg]['desc']
                data = las_conf[section][cfg]
                data.pop('desc', None)  # Remove cfg desc from user data
                cbox.insertItem(ncfg, txt, userData=data)
            grid.addWidget(cbox, 1, nsection)

            cfgd[section] = cbox

        apply_button = PyDMPushButton("Apply")
        apply_button.clicked.connect(
            lambda: self.apply_configuration(
                las_conf,
                las_db,
                cfgd['laser_rate_configs'],
                cfgd['goose_rate_configs'],
                cfgd['goose_arrival_configs']
            )
        )
        grid.addWidget(apply_button, 1, nsection+1)

        vlayout.addLayout(grid)

        # Finish the section
        line = PyDMDrawingLine()
        vlayout.addWidget(line)

        space = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vlayout.addItem(space)

    def apply_configuration(self, laser, laser_db, base, goose, arrival):

        self.set_tpr_configuration(laser, laser_db, base)
        # self.set_goose_configuration(laser, goose)
        # self.set_arrival_configuration(laser, arrival)

    def set_tpr_configuration(self, laser, laser_db, cbox):
        """
        Apply the given configuration to the TPR.

        Arguments
        ---------
        laser: The name of the laser configuration to be used.

        config: The rep rate configuration to be applied when calling this
                function.
        """
        rate_conf = cbox.currentData()
        tprs = laser_db.search(
                device_class='pcdsdevices.tpr.TprTrigger'
               )
        for tpr in tprs:
            name = tpr.metadata['name']
            if name in rate_conf:
                dev = tpr.get()
                print(dev)
                print(rate_conf[name])
                # dev.configure(rate_conf[key])

    def set_arrival_configuration(self, laser, laser_db, cbox):
        print(laser)

    def set_goose_configuration(self, laser, config):
        print(laser)
