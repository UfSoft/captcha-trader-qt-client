# -*- coding: utf-8 -*-
"""
    qtnam.utils.debug
    ~~~~~~~~~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import sys
import logging
import traceback
from qtnam.utils.i18n import _

log = logging.getLogger(__name__)

# Taken from http://bzimmer.ziclix.com/2008/12/17/python-thread-dumps/
def stacktraces():
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# ThreadID: %s" % threadId)
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                code.append("  %s" % (line.strip()))

    return "\n".join(code)


def install_core_except_hook():
    def custom_except_hook(exctype, value, tb):
        if isinstance(value, KeyboardInterrupt):
            log.info("KeyboardInterrupt caught. Exiting...")
            from PySide.QtCore import QCoreApplication
            QCoreApplication.instance().quit()

    sys.excepthook = custom_except_hook



def install_ui_except_hook():
    import os
    from PySide import QtCore, QtGui

    class ErrorReportDialog(QtGui.QDialog):
        def __init__(self, parent, error):
            flags = (QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint |
                     QtCore.Qt.WindowSystemMenuHint)
            QtGui.QDialog.__init__(self, parent, flags)
            self._setupUi()
            name = QtCore.QCoreApplication.applicationName()
            version = QtCore.QCoreApplication.applicationVersion()
            errorText = _("""\
Application Name: %(appname)s
Version: %(version)s

%(error)s""", appname=name, version=version, error=error)
            # Under windows, we end up with an error report without linesep if
            # we don't mangle it
            errorText = errorText.replace('\n', os.linesep)
            self.errorTextEdit.setPlainText(errorText)

            self.sendButton.clicked.connect(self.accept)
            self.dontSendButton.clicked.connect(self.reject)

        def _setupUi(self):
            self.setWindowTitle(_("Error Report"))
            self.resize(553, 349)
            self.verticalLayout = QtGui.QVBoxLayout(self)
            self.label = QtGui.QLabel(self)
            self.label.setText(
                _("Something went wrong. Would you like to send the error "
                  "report to UfSoft.org?")
            )
            self.label.setWordWrap(True)
            self.verticalLayout.addWidget(self.label)
            self.errorTextEdit = QtGui.QPlainTextEdit(self)
            self.errorTextEdit.setReadOnly(True)
            self.verticalLayout.addWidget(self.errorTextEdit)
            msg = _("Although the application should continue to run after "
                    "this error, it may be in an unstable state, so it is "
                    "recommended that you restart the application.")
            self.label2 = QtGui.QLabel(msg)
            self.label2.setWordWrap(True)
            self.verticalLayout.addWidget(self.label2)
            self.horizontalLayout = QtGui.QHBoxLayout()
            self.horizontalLayout.addItem(
                QtGui.QSpacerItem(
                    1, 1, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed
                )
            )
            self.dontSendButton = QtGui.QPushButton(self)
            self.dontSendButton.setText(_("Don't Send"))
            self.dontSendButton.setMinimumSize(QtCore.QSize(110, 0))
            self.horizontalLayout.addWidget(self.dontSendButton)
            self.sendButton = QtGui.QPushButton(self)
            self.sendButton.setText(_("Send"))
            self.sendButton.setMinimumSize(QtCore.QSize(110, 0))
            self.sendButton.setDefault(True)
            self.horizontalLayout.addWidget(self.sendButton)
            self.verticalLayout.addLayout(self.horizontalLayout)

        def accept(self):
            text = self.errorTextEdit.toPlainText()
            url = QtCore.QUrl(
                "mailto:projects@ufsoft.org?SUBJECT=Error Report&BODY=%s" % text
            )
            QtGui.QDesktopServices.openUrl(url)
            QtGui.QDialog.accept(self)

    def custom_except_hook(exctype, value, tb):
        if isinstance(value, KeyboardInterrupt):
            log.info("KeyboardInterrupt caught. Exiting...")
            from PySide.QtGui import QApplication
            QApplication.instance().quit()
            return

        s = ''.join(traceback.format_exception(exctype, value, tb))
        log.exception(s)
        dialog = ErrorReportDialog(None, s)
        dialog.exec_()

    sys.excepthook = custom_except_hook
