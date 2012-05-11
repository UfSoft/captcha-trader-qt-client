# -*- coding: utf-8 -*-
"""
    qtct.preferences
    ~~~~~~~~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import logging
from PySide import QtCore, QtGui
from qtct.ui import MaintainStateAndGeometry
from qtct.ui.preferences import Ui_PrefsDialog
from qtct.utils.i18n import get_available_locales, Translations

log = logging.getLogger(__name__)

@MaintainStateAndGeometry
class Preferences(QtGui.QDialog, Ui_PrefsDialog):

    Changed = QtCore.Signal()

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        settings = QtCore.QSettings()
        saved_locale = settings.value("locale")
        if not saved_locale:
            saved_locale = "en"

        for idx, locale in enumerate(get_available_locales()):
            self.languageCombo.addItem(locale.display_name, userData=str(locale))
            if str(locale)==saved_locale:
                self.languageCombo.setCurrentIndex(idx)

    def show(self):
        settings = QtCore.QSettings()
        self.username.setText(settings.value("username"))
        self.password.setText(settings.value("password"))
        if settings.value("solve_once_started"):
            self.solve_once_started.setChecked(
                settings.value("solve_once_started").lower()=='true'
            )
        else:
            self.solve_once_started.setChecked(False)
        if settings.value("start_minimized"):
            self.start_minimized.setChecked(
                settings.value("start_minimized").lower()=="true"
            )
        else:
            self.start_minimized.setChecked(False)
        if settings.value("credits_in_toolbar"):
            self.credits_in_toolbar.setChecked(
                settings.value("credits_in_toolbar").lower()=='true'
            )
        else:
            self.credits_in_toolbar.setChecked(False)

        QtGui.QDialog.show(self)

    @QtCore.Slot()
    def accept(self):
        log.info("Saving settings")
        settings = QtCore.QSettings()

        changed = False

        username = self.username.text()
        if username != settings.value("username"):
            settings.setValue("username", username)
            changed = True

        password = self.password.text()
        if password != settings.value("password"):
            settings.setValue("password", password)
            changed = True

        start_minimized = self.start_minimized.isChecked()
        if start_minimized != settings.value("start_minimized"):
            settings.setValue("start_minimized", start_minimized)
            changed = True

        solve_once_started = self.solve_once_started.isChecked()
        if solve_once_started != settings.value("solve_once_started"):
            settings.setValue("solve_once_started", solve_once_started)
            changed = True

        credits_in_toolbar = self.credits_in_toolbar.isChecked()
        if credits_in_toolbar != settings.value("credits_in_toolbar"):
            settings.setValue("credits_in_toolbar", credits_in_toolbar)
            changed = True

        locale = self.languageCombo.itemData(self.languageCombo.currentIndex())
        if locale != settings.value("locale"):
            settings.setValue("locale", locale)
            QtGui.qApp.locale = locale
            QtGui.qApp.translations = Translations.load()
#            self.languageChange()
            self.parent().languageChange()
            changed = True

        QtGui.QDialog.accept(self)
        if changed:
            self.Changed.emit()

    @QtCore.Slot()
    def reject(self):
        log.info("Settings not saved")
        QtGui.QDialog.reject(self)

