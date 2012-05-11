# -*- coding: utf-8 -*-
"""
    qtct.mainwindow
    ~~~~~~~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import logging
from PySide import QtCore, QtGui
from qtct import __version__
from qtct.captchasolver import CaptchaSolver
from qtct.preferences import Preferences
from qtct.ui import MaintainStateAndGeometry
from qtct.ui.mainwindow import Ui_MainWindow
from qtct.utils.i18n import Translations, _

log = logging.getLogger(__name__)

COL_ID, COL_CAPTCHA, COL_SOLUTION, COL_CORRECT = range(4)
CAPTCHA_STATUS_ICONS = {
    None: QtGui.QPixmap(":/captcha_wait.png"),
    False: QtGui.QPixmap(":/captcha_failed.png"),
    True: QtGui.QPixmap(":/captcha_ok.png"),
    "": QtGui.QPixmap(":/captcha_skipped.png"),
}

class AboutDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.vbox = QtGui.QVBoxLayout()
        self.vbox.setSpacing(15)
        self.vbox.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)
        self.vbox.setContentsMargins(15, 15, 15, 15)
        self.setLayout(self.vbox)

        self.logo = QtGui.QLabel()
        self.logo.setAlignment(QtCore.Qt.AlignCenter)
        self.logo.setPixmap(QtGui.QPixmap(":/logo_big.png"))
        self.vbox.addWidget(self.logo)

        self.appname = QtGui.QLabel(_("Captcha Trader Qt Client"))
        self.appname.setAlignment(QtCore.Qt.AlignCenter)
        font = self.font()
        fontsize = font.pointSize()
        font.setPointSize(fontsize+10)
        self.appname.setFont(font)
        self.vbox.addWidget(self.appname)

        self.appversion = QtGui.QLabel(__version__)
        self.appversion.setAlignment(QtCore.Qt.AlignCenter)
        font = self.font()
        fontsize = font.pointSize()
        font.setPointSize(fontsize+5)
        self.appversion.setFont(font)
        self.vbox.addWidget(self.appversion)

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.vbox.addWidget(self.buttonBox)

        QtCore.QObject.connect(
            self.buttonBox, QtCore.SIGNAL("accepted()"), self.accept
        )
        QtCore.QObject.connect(
            self.buttonBox, QtCore.SIGNAL("rejected()"), self.reject
        )

        self.setWindowTitle(_("About"))


class CaptchaImageDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        try:
            pixmap = index.data()
            if isinstance(pixmap, QtGui.QImage):
                pixmap = QtGui.QPixmap.fromImage(pixmap)

            rect = option.rect
            x = rect.x()
            y = rect.y()
            width = rect.width()
            height = rect.height()

            if height > pixmap.height():
                rest = height - pixmap.height()
                height = pixmap.height()
                y += int(rest/2)

            if width > pixmap.width():
                rest = width - pixmap.width()
                width = pixmap.width()
                x += int(rest/2)

            painter.drawPixmap(x, y, width, height, pixmap)
        except AttributeError:
            return QtGui.QStyledItemDelegate.paint(self, painter, option, index)


    def sizeHint(self, option, index):
        try:
            size = index.data().size()
            height = size.height()
            if height < 56:
                height = 56
            return QtCore.QSize(size.width(), height)
        except AttributeError:
            return QtGui.QStyledItemDelegate.sizeHint(self, option, index)

class StatusImageDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        pixmap = index.data()
        if isinstance(pixmap, QtGui.QImage):
            pixmap = QtGui.QPixmap.fromImage(pixmap)

        rect = option.rect
        x = rect.x()
        y = rect.y()
        width = rect.width()
        height = rect.height()

        if height > 56:
            rest = height - 56
            y += int(rest/2.0)

        if width > 56:
            rest = rect.width() - 56
            x += int(rest/2.0)

        painter.drawPixmap(x, y, 56, 56, pixmap)

    def sizeHint(self, option, index):
        return QtCore.QSize(56, 56)


class SolvedCaptchasModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 4, parent)
        self.__captchas = {}
        self.CAPTCHA_STATUS_TOOLTIPS = {
            None: _("Waiting"),
            False: _("Failed"),
            True: _("Correct"),
            "": _("Skipped"),
        }

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Set the headers to be displayed. """
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            if section == COL_ID:
                return _("Ticket ID")
            elif section == COL_CAPTCHA:
                return _("Captcha")
            elif section == COL_SOLUTION:
                return _("Solution")
            elif section == COL_CORRECT:
                return _("Status")

        return None

    def add_captcha(self, captcha):
        row = self.rowCount()
        self.insertRows(row, 1, QtCore.QModelIndex())
        self.__captchas[captcha.ticket_id] = row
        self.parent().setRowHeight(60, row)

        ix = self.index(row, COL_ID, QtCore.QModelIndex())
        self.setData(ix, captcha.ticket_id, QtCore.Qt.EditRole)

        ix = self.index(row, COL_CAPTCHA, QtCore.QModelIndex())
        self.setData(ix, captcha.image, QtCore.Qt.EditRole)

        ix = self.index(row, COL_SOLUTION, QtCore.QModelIndex())
        self.setData(ix, captcha.solution, QtCore.Qt.EditRole)

        ix = self.index(row, COL_CORRECT, QtCore.QModelIndex())
        if captcha.wasSkipped():
            self.setData(ix, CAPTCHA_STATUS_ICONS[""], QtCore.Qt.EditRole)
            self.setData(ix, self.CAPTCHA_STATUS_TOOLTIPS[""], QtCore.Qt.ToolTipRole)

        else:
            self.setData(ix, CAPTCHA_STATUS_ICONS[captcha.correct], QtCore.Qt.EditRole)
            self.setData(ix, self.CAPTCHA_STATUS_TOOLTIPS[captcha.correct], QtCore.Qt.ToolTipRole)
        return row

    def set_captcha_result(self, captcha):
        if captcha.ticket_id not in self.__captchas:
            return
        row = self.__captchas[captcha.ticket_id]
        ix = self.index(row, COL_CORRECT, QtCore.QModelIndex())
        self.setData(ix, CAPTCHA_STATUS_ICONS[captcha.correct], QtCore.Qt.EditRole)
        self.setData(ix, self.CAPTCHA_STATUS_TOOLTIPS[captcha.correct], QtCore.Qt.ToolTipRole)
        return row


class BaseBarWidget(QtGui.QWidget):
    def __init__(self, label, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.setSpacing(3)
        self.hbox.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.hbox)

        self.separator = QtGui.QFrame()
        self.separator.setGeometry(QtCore.QRect(320, 150, 118, 3))
        self.separator.setFrameShape(QtGui.QFrame.VLine)
        self.separator.setFrameShadow(QtGui.QFrame.Sunken)
        self.hbox.addWidget(self.separator)

        self.defaultFontSize = self.font().pointSize()

        self.label = QtGui.QLabel(label)
        self.hbox.addWidget(self.label)
        self.value = QtGui.QLabel(_("Not Available"))
        self.hbox.addWidget(self.value)

    def show(self):
        font = self.font()
        if isinstance(self.parent(), QtGui.QStatusBar):
            font.setPointSize(self.defaultFontSize)
            self.separator.show()
        else:
            font.setPointSize(self.defaultFontSize+8)
            self.separator.hide()
        self.setFont(font)
        QtGui.QWidget.show(self)

    def setValue(self, value):
        self.value.setText(value)

class CreditsWidget(BaseBarWidget):
    def __init__(self, parent=None):
        BaseBarWidget.__init__(self, _("Credits:"), parent)

class WaitTimeWidget(BaseBarWidget):
    def __init__(self, parent=None):
        BaseBarWidget.__init__(self, _("Next Captcha:"), parent)

    def setValue(self, value):
        if value <= 10:
            value = "<font color=\"red\">%s</font>" % value
        BaseBarWidget.setValue(self, _("%(secs)s secs", secs=value))


@MaintainStateAndGeometry
class MainWindow(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self, application):
        QtGui.QMainWindow.__init__(self)
        self.application = application

        self.set_application_attributes()

        self.setupUi()

        self.setup_client()
        self.setup_solver()
        self.setup_preferences()
        self.setup_actions()
        self.setup_systray()
        self.tootip_timer = QtCore.QTimer()
        self.tootip_timer.setInterval(1000)
        self.tootip_timer.timeout.connect(self.update_tooltip)
        self.__queue_pos = self.__wait_time = None

    def setupUi(self):
        super(MainWindow, self).setupUi(self)

        newFont = self.font()
        defaultSize = newFont.pointSize()
        newFont = self.font()
        newFont.setPointSize(defaultSize+8)
        self.solutionsTable.setFont(newFont)

        newFont = self.font()
        newFont.setPointSize(defaultSize)
        self.solutionsTable.horizontalHeader().setFont(newFont)

        self.model = SolvedCaptchasModel(self.solutionsTable)
        self.solutionsTable.setModel(self.model)

        self.solutionsTable.horizontalHeader().setResizeMode(
            COL_ID, QtGui.QHeaderView.ResizeToContents
        )
        self.solutionsTable.horizontalHeader().setResizeMode(
            COL_CAPTCHA, QtGui.QHeaderView.ResizeToContents
        )
        self.solutionsTable.horizontalHeader().setResizeMode(
            COL_SOLUTION, QtGui.QHeaderView.Stretch
        )
        self.solutionsTable.setItemDelegateForColumn(
            COL_CAPTCHA, CaptchaImageDelegate(self)
        )
        self.solutionsTable.setItemDelegateForColumn(
            COL_CORRECT, StatusImageDelegate(self)
        )


        self.creditsWidget = CreditsWidget(self)
        self.waitTimeWidget = WaitTimeWidget(self)
        self.waitTimeWidget.hide()

        settings = QtCore.QSettings()

        if settings.value("credits_in_toolbar") and \
                        settings.value("credits_in_toolbar").lower() == "true":

            self.creditsTbWidget = QtGui.QWidget()
            self.creditsLayout = QtGui.QHBoxLayout()
            self.creditsLayout.setSpacing(3)
            self.creditsLayout.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)
            self.creditsLayout.setContentsMargins(0, 0, 0, 0)
            self.creditsLayout.setObjectName("horizontalLayout")
            self.creditsTbWidget.setLayout(self.creditsLayout)

            spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
            self.creditsLayout.addItem(spacerItem)

            self.creditsLayout.addWidget(self.waitTimeWidget)
            self.creditsLayout.addSpacing(20)
            self.creditsLayout.addWidget(self.creditsWidget)
            self.creditsLayout.addSpacing(10)
            self.toolBar.addWidget(self.creditsTbWidget)

        else:
            self.statusbar.addPermanentWidget(self.waitTimeWidget)
            self.statusbar.addPermanentWidget(self.creditsWidget)

        self.model.rowsInserted.connect(self.on_model_rowsInserted)

        self.about = AboutDialog(self)


    def set_application_attributes(self):
        QtCore.QCoreApplication.setOrganizationName("UfSoft.org")
        QtCore.QCoreApplication.setOrganizationDomain("UfSoft.org")
        QtCore.QCoreApplication.setApplicationName("CaptchaTrader")

        settings = QtCore.QSettings()
        locale = settings.value("locale")
        if not locale:
            settings.setValue("locale", "en")
        locale = settings.value("locale")
        self.application.locale = locale
        self.application.translations = Translations.load()

    def setup_client(self):
        from qtct.client import CaptchaTrader
        settings = QtCore.QSettings()
        self.client = CaptchaTrader(
            self, settings.value("username"), settings.value("password")
        )
        self.client.StateChanged.connect(self.on_client_state_changed)
        self.client.GotWaitTime.connect(self.on_client_waittime)
        self.client.Exited.connect(QtGui.qApp.quit)

        self.client.GotCredits.connect(self.on_client_GotCredits)
        self.client.SolvedCaptcha.connect(self.on_client_SolvedCaptcha)
        self.client.SolvedCaptchaResponse.connect(self.on_client_SolvedCaptchaResponse)

    def setup_solver(self):
        self.solver = CaptchaSolver(self)

    def setup_preferences(self):
        self.prefs = Preferences(self)
        self.prefs.Changed.connect(self.on_preferences_changed)

    def setup_actions(self):
        self.actionStart.triggered.connect(self.client.start)
        self.actionStop.triggered.connect(self.client.stop)
        self.actionStop.setEnabled(False)
        self.actionPreferences.triggered.connect(self.show_preferences)
        self.actionQuit.triggered.connect(self.quit)
        self.actionAbout.triggered.connect(self.show_about)

    def setup_systray(self):
        self.systray_menu = QtGui.QMenu(self)
        self.systray_menu.addAction(self.actionShowClient)
        self.systray_menu.addSeparator()
        self.systray_menu.addAction(self.actionStart)
        self.systray_menu.addAction(self.actionStop)
        self.systray_menu.addSeparator()
        self.systray_menu.addAction(self.actionPreferences)
        self.systray_menu.addAction(self.actionQuit)

        self.tray_icon = QtGui.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QPixmap(":/logo.png"))
        self.tray_icon.setContextMenu(self.systray_menu)
        self.tray_icon.activated.connect(self.on_systray_activated)
        self.tray_icon.show()

    def show_about(self):
        if self.about.isVisible():
            self.about.hide()
        else:
            self.about.show()

    def show_preferences(self):
        if self.prefs.isVisible():
            self.prefs.hide()
        else:
            self.prefs.show()

    def on_preferences_changed(self):
        settings = QtCore.QSettings()
        self.client.username = settings.value("username")
        self.client.password = settings.value("password")

    def on_client_state_changed(self, prev, state):
        from qtct.client import STATE_ENQUEUED
        self.actionStart.setDisabled(self.client.isRunning())
        self.actionStop.setEnabled(self.client.isRunning())
        if not self.client.isRunning():
            self.tray_icon.setToolTip(_("Client Stopped"))
            self.tootip_timer.stop()
        else:
            self.tray_icon.setToolTip(_("Starting client"))
            if not self.tootip_timer.isActive():
                self.tootip_timer.start()

        if state == STATE_ENQUEUED and not self.tootip_timer.isActive():
            self.tootip_timer.start()

        self.waitTimeWidget.setVisible(state==STATE_ENQUEUED)


    def on_client_waittime(self, queue, secs):
        self.__queue_pos = queue
        self.__wait_time = secs
        self.waitTimeWidget.setValue(secs)
        self.tootip_timer.stop()
        QtCore.QTimer.singleShot(50, self.tootip_timer.start)
        self.waitTimeWidget.show()


    def on_client_SolvedCaptcha(self, captcha):
        self.model.add_captcha(captcha)
        self.solutionsTable.resizeRowsToContents()


    def on_client_SolvedCaptchaResponse(self, captcha):
        self.model.set_captcha_result(captcha)
        self.solutionsTable.resizeRowsToContents()

    def on_client_GotCredits(self, credits):
        self.creditsWidget.setValue(str(credits))

    def on_systray_activated(self, reason):
        if reason == QtGui.QSystemTrayIcon.DoubleClick:
            self.actionShowClient.toggle()

    def update_tooltip(self):
        if self.__queue_pos is not None and self.__wait_time is not None:
            self.__wait_time -= 1
            if self.__wait_time < 0:
                self.__wait_time = 1
            tooltip = _("Credits: %(credits)s<br>Queue position: %(queue_pos)s"
                        "<br>Waiting for %(secs)s seconds.",
                        credits=self.client.credits,
                        queue_pos=self.__queue_pos,
                        secs=self.__wait_time)
            self.waitTimeWidget.setValue(self.__wait_time)

        elif self.__wait_time is not None and self.__wait_time <= 0:
            tooltip = ""
            self.waitTimeWidget.setValue(0)
            self.__wait_time = self.__queue_pos = None
        else:
            tooltip = ""
            self.tootip_timer.stop()

        self.systray_menu.setToolTip(tooltip)
        self.tray_icon.setToolTip(tooltip)

    def run(self):
        settings = QtCore.QSettings()
        if not settings.value("username") or not settings.value("password"):
            QtCore.QTimer.singleShot(1000, self.show_preferences)
        elif settings.value("solve_once_started") and \
                        settings.value("solve_once_started").lower() == "true":
            QtCore.QTimer.singleShot(1000, self.client.start)

        if settings.value("start_minimized") and \
                            settings.value("start_minimized").lower() != "true":
            self.actionShowClient.toggle()

        log.info("Application is running")
        return self.application.exec_()

    def quit(self):
        self.tootip_timer.stop()
        if self.client.isRunning():
            self.client.Exited.connect(QtGui.qApp.quit)
            self.client.quit()
        else:
            QtGui.qApp.quit()

    def closeEvent(self, event):
        self.actionShowClient.toggle()
        event.accept()

    def languageChange(self):
        return QtGui.QMainWindow.languageChange(self)

    def on_model_rowsInserted(self, *args):
        QtCore.QTimer.singleShot(150, self.solutionsTable.scrollToBottom)

