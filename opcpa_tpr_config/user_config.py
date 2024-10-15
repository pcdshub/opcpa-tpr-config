import logging
from typing import Optional

from qtpy import QtWidgets
from widgets import UserConfigDisplay

logger = logging.getLogger(__name__)


def main(
    config: str = "",
    stylesheet: Optional[str] = None
) -> None:
    """Launch the ``Rep. rate user config UI``."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    try:
        widget = UserConfigDisplay(config=config)
        widget.show()
    except Exception:
        logger.exception("Failed to load user interface")
    app.exec_()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="Yaml config file for user UI", type=str
    )
    args = parser.parse_args()

    main(config=args.config)
