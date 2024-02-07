import yaml

from functools import partial

from qtpy.QtWidgets import QGridLayout

from ophyd import EpicsSignal

from pydm import Display
from pydm.widgets import (PyDMLabel, PyDMShellCommand, PyDMPushButton,
                          PyDMNTTable)

class App(Display):

    def __init__(self, parent=None, args=None, macros=None):
        print('Start of __init__ for template launcher')
        print(f'args={args}, macros={macros}')

        # Read in config file
        cfg_file = "opcpa-tpr-config/neh_config.yaml" #TODO add argparse, make this an arg

        config = {}
        with open(cfg_file, 'r') as f:
            config = yaml.safe_load(f)
        self.config = config

        print(f'Loaded config {cfg_file}:')
        print(config)

        # Call super after handling args/macros but before doing pyqt stuff
        super().__init__(parent=parent, args=args, macros=macros)

        # Now it is safe to refer to self.ui and access your widget objects
        # It is too late to do any macros processing

        # Setup main areas of GUI
        self.setup_main()

        # Setup laser specific portions of GUI
        for laser in self.config['lasers']:
            self.setup_channels(laser)
            self.setup_configs(laser)

        print('End of __init__ for template launcher')

    def ui_filename(self):
        return 'opcpa-tpr-config.ui'
 
    def setup_main(self):
        title = self.findChild(PyDMLabel, 'screen_title')
        if title is not None:
            title.setText(self.config['main']['title'])
        xpm_label = self.findChild(PyDMLabel, 'xpm_label')
        xpm_pv = self.config['main']['xpm_pv']
        if xpm_label is not None:
            xpm_label.setText(xpm_pv)
        xpm = self.findChild(PyDMNTTable, 'xpm')
        if xpm is not None:
            xpm.set_channel(f'pva://{xpm_pv}')

    def setup_channels(self, laser):
        grid = self.ui.findChild(QGridLayout, f'{laser}_trig_layout')
        if grid is not None:
            # Setup column headers
            desc = PyDMLabel()
            desc.setText('Trigger')
            grid.addWidget(desc, 0, 0)
            reprate = PyDMLabel()
            reprate.setText('Rep. Rate')
            grid.addWidget(reprate, 0, 1)
            ratemode = PyDMLabel()
            ratemode.setText('Rate Mode')
            grid.addWidget(ratemode, 0, 2)
            eventcode = PyDMLabel()
            eventcode.setText('Event Code')
            grid.addWidget(eventcode, 0, 3)
            
            # Setup PV RBVs
            las = self.config['lasers'][laser]
            las_conf = self.config[las]
            child = self.findChild(PyDMLabel, f'{laser}_desc')
            if child is not None:
                child.setText(las_conf['laser_desc'])
            tpr_base = las_conf['tpr_base']
            labels = ['DESC', 'RATE', 'RATEMODE', 'SEQCODE']
            for nchannel, channel in enumerate(las_conf['channels'], start=1):
                for nlabel, label in enumerate(labels):
                    child = PyDMLabel()
                    if label == 'DESC':
                        val = las_conf['channels'][f'{channel}']['desc']
                        child.setText(val)
                    else:
                        tpr_ch = las_conf['channels'][f'{channel}']['ch']
                        child.set_channel(f'ca://{tpr_base}:CH{tpr_ch}_{label}')
                    grid.addWidget(child, nchannel, nlabel)
        else:
            print("Laser {} not found!".format(laser))

         
    def setup_configs(self, laser):
        grid = self.findChild(QGridLayout, f"{laser}_config_layout") 
        if grid is not None:
            las = self.config['lasers'][laser]
            for ncfg, cfg in enumerate(self.config[las]['rate_configs']):
                button = PyDMPushButton(f'{laser}_{cfg}')
                rate = self.config[las]['rate_configs'][cfg]['rate']
                button.setText(f'{rate}')
                row, col = divmod(ncfg, 4)
                row += 1 # Leave first row for title
                grid.addWidget(button, row, col)
                button.clicked.connect(partial(self.set_configuration, las, cfg))

    def set_configuration(self, laser, config):
        """Apply the given configuration to the TPR"""
        cfg = self.config[laser]['rate_configs'][config]
        tpr_base = self.config[laser]['tpr_base']
        for channel in self.config[laser]['channels']:
            if channel in self.config[laser]['rate_configs'][config]:
                tpr_ch = self.config[laser]['channels'][f'{channel}']['ch']
                # Set rate mode
                ratemode_val = self.config[laser]['rate_configs'][config][channel]['ratemode']
                ratemode_sig = EpicsSignal(f'{tpr_base}:CH{tpr_ch}_RATEMODE')
                ratemode_sig.put(ratemode_val)
                # Set rate
                rate_val = self.config[laser]['rate_configs'][config][channel]['rate']
                if ratemode_val == 'Fixed':
                    rate_sig = EpicsSignal(f'{tpr_base}:CH{tpr_ch}_FIXEDRATE')
                    rate_sig.put(rate_val)
                elif ratemode_val == 'Seq':
                    rate_sig = EpicsSignal(f'{tpr_base}:CH{tpr_ch}_SEQCODE')
                    event_code = self.config[laser]['rep_rates'][rate_val]
                    rate_sig.put(event_code)
                else:
                    raise ValueError(f"Unknown ratemode {ratemode_val}")
                # Enable/Disable the trigger
                enable_val = self.config[laser]['rate_configs'][config][channel]['enable']
                trg_sig = EpicsSignal(f'{tpr_base}:TRG{tpr_ch}_SYS2_TCTL')
                trg_sig.put(enable_val)
                ch_sig = EpicsSignal(f'{tpr_base}:CH{tpr_ch}_SYS2_TCTL')
                ch_sig.put(enable_val)
