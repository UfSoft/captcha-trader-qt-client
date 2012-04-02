# -*- coding: utf-8 -*-
"""
    qtct.preferences
    ~~~~~~~~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import logging
from PySide import QtCore, QtGui
from qtct.ui.preferences import Ui_PrefsDialog

log = logging.getLogger(__name__)

class Preferences(QtGui.QDialog, Ui_PrefsDialog):

    Changed = QtCore.Signal()

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

    def show(self):
        settings = QtCore.QSettings()
        self.username.setText(settings.value("username"))
        self.password.setText(settings.value("password"))
        self.solve_once_started.setChecked(
            settings.value("solve_once_started") and True or False
        )
        QtGui.QDialog.show(self)

    @QtCore.Slot()
    def accept(self):
        log.info("Accepted")
        settings = QtCore.QSettings()
        username = self.username.text()
        if username != settings.value("username"):
            settings.setValue("username", username)
        password = self.password.text()
        if password != settings.value("password"):
            settings.setValue("password", password)
        solve_once_started = self.solve_once_started.isChecked()
        if solve_once_started != settings.value("solve_once_started"):
            settings.setValue("solve_once_started", solve_once_started)
        QtGui.QDialog.accept(self)

    @QtCore.Slot()
    def reject(self):
        log.info("rejected")
        QtGui.QDialog.reject(self)

