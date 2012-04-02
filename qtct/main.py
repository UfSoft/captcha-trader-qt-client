# -*- coding: utf-8 -*-
"""
    qtct.main
    ~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

from PySide import QtGui


def main():
    import sys

    qtapp = QtGui.QApplication([a for a in sys.argv if a])


    from qtct.utils.i18n import _

    if not QtGui.QSystemTrayIcon.isSystemTrayAvailable():
        QtGui.QMessageBox.critical(
            None, _("Systray"),
            _("I couldn't detect any system tray on this system.")
        )
        sys.exit(1)

    QtGui.QApplication.setQuitOnLastWindowClosed(False)


    from optparse import OptionParser
    import qtct
    from qtct.application import Application
    from qtct.utils import log
    parser = OptionParser("qt-captcha-trader", version=qtct.__version__)
    parser.add_option(
        '-L', '--loglevel', default="info", choices=sorted(
            log.LOG_LEVELS, key=lambda k: log.LOG_LEVELS[k]
        ), help="The desired logging level. Default: %default"
    )

    (options, args) = parser.parse_args()
    log.setup_console_logger(options.loglevel, increase_padding=True)
    import logging
    logging.getLogger("qtct.main").info("Starting application")

    app = Application(qtapp)

    from qtct.utils.debug import install_ui_except_hook
    install_ui_except_hook()
    sys.exit(app.run())
