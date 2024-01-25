import sys
from pathlib import Path

import pydm
from pydm.utilities import setup_renderer


def main():
    print('launching from main')
    setup_renderer()

    app = pydm.PyDMApplication(
        ui_file=str(Path(__file__).parent / 'appname.py'),
        command_line_args=[],
        display_args=[],
        perfmon=False,
        hide_nav_bar=True,
        hide_menu_bar=True,
        hide_status_bar=True,
        fullscreen=False,
        read_only=True,
        macros=False,
        stylesheet_path=None,
    )

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
