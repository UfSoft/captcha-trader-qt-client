# -*- coding: utf-8 -*-
"""
    qtct.application
    ~~~~~~~~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import logging
from PySide import QtCore, QtGui

from qtct.client import CaptchaTrader
from qtct.preferences import Preferences
from qtct.captchasolver import CaptchaSolver
from qtct.solvedcaptchas import SolvedCaptchas
from qtct.utils.i18n import _

log = logging.getLogger(__name__)

class Application(QtGui.QWidget):
    def __init__(self, application):
        QtGui.QWidget.__init__(self)
        self.application = application
        self.set_application_attributes()
        self.setup_client()
        self.setup_solver()
        self.setup_preferences()
        self.setup_solutions()
        self.create_actions()
        self.setup_systray()
        self.tootip_timer = QtCore.QTimer()
        self.tootip_timer.setInterval(1000)
        self.tootip_timer.timeout.connect(self.update_tooltip)
        self.__queue_pos = self.__wait_time = None


    def set_application_attributes(self):
        QtCore.QCoreApplication.setOrganizationName("UfSoft.org")
#        self.parent().setOrganizationName("pyLoad")
        QtCore.QCoreApplication.setOrganizationDomain("UfSoft.org")
#        self.parent().setOrganizationDomain("UfSoft.org")
        QtCore.QCoreApplication.setApplicationName("CaptchaTrader")
#        self.parent().setApplicationName("CaptchaTrader")
#        self.parent().setWindowIcon(QtGui.QPixmap(":/logo.png"))

    def run(self):
#        self.tootip_timer.start()
        settings = QtCore.QSettings()
        print 890, settings.value("solve_once_started"), settings.value("solve_once_started")==True
        if settings.value("solve_once_started") == "True":
            QtCore.QTimer.singleShot(1000, self.client.start)
        return self.application.exec_()

    def quit(self):
        self.tootip_timer.stop()
        if self.client.isRunning():
            print 890
            self.client.Exited.connect(QtGui.qApp.quit)
            self.client.quit()
        else:
            QtGui.qApp.quit()

    def create_actions(self):
        self.startAction = QtGui.QAction("St&art Solving", self, triggered=self.client.start)
        self.stopAction = QtGui.QAction("St&op Solving", self, triggered=self.client.stop)
        self.prefsAction = QtGui.QAction("&Preferences", self, triggered=self.show_preferences)
        self.statsAction = QtGui.QAction("&Solutions", self, triggered=self.show_solutions)
        self.quitAction = QtGui.QAction("&Quit", self, triggered=self.quit)
        self.stopAction.setEnabled(False)

    def setup_systray(self):
        self.systray_menu = QtGui.QMenu(self)
        self.systray_menu.addAction(self.startAction)
        self.systray_menu.addAction(self.stopAction)
        self.systray_menu.addAction(self.statsAction)
        self.systray_menu.addSeparator()
        self.systray_menu.addAction(self.prefsAction)
        self.systray_menu.addAction(self.quitAction)

        self.tray_icon = QtGui.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QPixmap(":/logo.svg"))
        self.tray_icon.setContextMenu(self.systray_menu)
        self.tray_icon.show()

    def setup_preferences(self):
        self.prefs = Preferences(self)
        self.prefs.Changed.connect(self.on_preferences_changed)

    def setup_solutions(self):
        self.solutions = SolvedCaptchas(self)

    def show_preferences(self):
        if self.prefs.isVisible():
            self.prefs.hide()
        else:
            self.prefs.show()

    def show_solutions(self):
        if self.solutions.isVisible():
            self.solutions.hide()
        else:
            self.solutions.show()

    def on_preferences_changed(self):
        settings = QtCore.QSettings()
        self.client.username = settings.value("username")
        self.client.password = settings.value("password")

    def setup_client(self):
        settings = QtCore.QSettings()
        self.client = CaptchaTrader(
            self, settings.value("username"), settings.value("password")
        )
        self.client.StateChanged.connect(self.on_client_state_changed)
        self.client.GotWaitTime.connect(self.on_client_waittime)
        self.client.Exited.connect(QtGui.qApp.quit)

    def setup_solver(self):
        self.solver = CaptchaSolver(self)

    def on_client_state_changed(self, prev, state):
        self.startAction.setDisabled(self.client.isRunning())
        self.stopAction.setEnabled(self.client.isRunning())
        if not self.client.isRunning():
            self.tray_icon.setToolTip(_("Client Stopped"))
            self.tootip_timer.stop()
        else:
            self.tray_icon.setToolTip("Starting client")
            self.tootip_timer.start()

    def on_client_waittime(self, queue, secs):
        self.__queue_pos = queue
        self.__wait_time = secs

    def update_tooltip(self):
        if self.__queue_pos is not None and self.__wait_time is not None:
            self.__wait_time -= 1
#            tooltip = _("Waiting for %s seconds. Queue position: %s" % (
#                        self.__wait_time, self.__queue_pos))
            tooltip = _("Credits: %s<br>Queue position: %s<br>Waiting for %s seconds. " % (
                        self.client.credits, self.__queue_pos, self.__wait_time))
        elif self.__wait_time < 0:
            tooltip = ""
            self.__wait_time = self.__queue_pos = None
        else:
            tooltip = ""
        self.systray_menu.setToolTip(tooltip)
        self.tray_icon.setToolTip(tooltip)
