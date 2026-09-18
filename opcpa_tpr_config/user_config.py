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
        help="Enable debug-level logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
    )
    log_level = logging.DEBUG if args.debug else logging.INFO
    loggers = [
        logging.getLogger("widgets"),
        logging.getLogger("xpm_prog")
    ]
    for logger in loggers:
        logger.setLevel(log_level)

    main(config=args.config)
