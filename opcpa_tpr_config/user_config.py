import logging
from typing import Optional

from qtpy import QtWidgets
from widgets import UserConfigDisplay

logger = logging.getLogger(__name__)


def main(
    config: str = "",
    debug: bool = False,
    stylesheet: Optional[str] = None
) -> None:
    """Launch the ``Rep. rate user config UI``."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    try:
        widget = UserConfigDisplay(config=config, debug=debug)
        widget.show()
        app.exec_()
    except Exception:
        logger.exception("Failed to load user interface")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="Yaml config file for user UI", type=str
    )
    parser.add_argument(
        "-d", "--debug", action='store_true',
        help="Print debug information, do not change settings"
    )
    args = parser.parse_args()

    main(config=args.config, debug=args.debug)
