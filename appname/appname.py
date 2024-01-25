from pydm import Display


class App(Display):

    def __init__(self, parent=None, args=None, macros=None):
        print('Start of __init__ for template launcher')
        print(f'args={args}, macros={macros}')
        # Call super after handling args/macros but before doing pyqt stuff
        super().__init__(parent=parent, args=args, macros=macros)
        # Now it is safe to refer to self.ui and access your widget objects
        # It is too late to do any macros processing
        print('End of __init__ for template launcher')

    def ui_filename(self):
        return 'appname.ui'
