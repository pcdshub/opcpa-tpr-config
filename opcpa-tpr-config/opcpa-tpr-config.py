import yaml

from pydm import Display
from pydm.widgets import PyDMLabel

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

        for laser in self.config['lasers']:
            self.setup_laser(laser)

        print('End of __init__ for template launcher')

    def ui_filename(self):
        return 'opcpa-tpr-config.ui'
   
    def setup_laser(self, laser):
        #confd = self.config.get(laser)[0]
        las = self.config['lasers'][laser]
        if las is not None:
            las_conf = self.config[las]
            channels = range(1, 4)
            tpr_prefix = las_conf['tpr_prefix']
            labels = ['DESC', 'RATE', 'RATEMODE', 'SEQCODE']
            for channel in channels:
                for label in labels:
                    child = self.findChild(PyDMLabel, "{}_ch{}_{}".format(laser, channel, label))
                    if child is not None:
                        if label == 'DESC':
                            val = las_conf[f'ch{channel}_{label}']
                            child.setText(val)
                        else:
                            tpr_ch = las_conf[f'ch{channel}_ch'] 
                            child.set_channel(f'ca://{tpr_prefix}:{tpr_ch}_{label}')
        else:
            print("Laser {} not found!".format(laser))
