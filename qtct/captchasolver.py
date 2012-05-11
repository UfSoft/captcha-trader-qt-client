# -*- coding: utf-8 -*-
"""
    qtct.solver
    ~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import logging
from PySide import QtCore, QtGui
from qtct.ui.captchasolver import Ui_CaptchaSolverDialog

log = logging.getLogger(__name__)

class CaptchaSolver(QtGui.QDialog, Ui_CaptchaSolverDialog):

    NewCaptcha = QtCore.Signal(object)

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
#        self.setWindowFlags(
#            QtCore.Qt.Dialog | QtCore.Qt.X11BypassWindowManagerHint |
#            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
#        )
        self.setupUi(self)
        newFont = self.font()
        newFont.setPointSize(newFont.pointSize() + 3)
        self.setFont(newFont)
        newFont.setPointSize(newFont.pointSize() + 3)
        self.captchaSolution.setFont(newFont)
        self.parent().client.NewCaptcha.connect(self.NewCaptcha.emit)
        self.NewCaptcha.connect(self.on_client_NewCaptcha)
        self.counter = 0
        self.counter_timer = QtCore.QTimer()
        self.counter_timer.setInterval(1000)
        self.counter_timer.timeout.connect(self.on_timer_timeout)
        self.keypress_timer = QtCore.QTimer()
        self.keypress_timer.setInterval(1000)
        self.keypress_timer.setSingleShot(True)
        self.keypress_timer.timeout.connect(self.on_keypress_timer_timeout)
        self.captchaSolution.textEdited.connect(self.on_keypress)

#    @QtCore.Slot(int, QtGui.QImage)
    def on_client_NewCaptcha(self, captchaticket):
        self.captchaSolution.setText("")
        self.solveButton.setEnabled(False)
        self.__current_jib = captchaticket.ticket_id
        self.captchaLabel.setPixmap(QtGui.QPixmap.fromImage(captchaticket.image))
        self.resize(10, 10)
        self.adjustSize()
        self.counter = 21
        self.on_timer_timeout()
        self.counter_timer.start()
        self.show()


    def accept(self):
        if self.__current_jib:
            log.info("Submitting captcha solution %r for ticket it %s",
                     self.captchaSolution.text(), self.__current_jib)
            if self.captchaSolution.text()=="":
                self.parent().client.skip(self.__current_jib)
            else:
                self.parent().client.answer(
                    self.__current_jib, self.captchaSolution.text()
                )
            self.__current_jib = None
        self.counter_timer.stop()
        QtGui.QDialog.accept(self)

    def on_keypress(self):
        if self.counter_timer.isActive():
            self.counter_timer.stop()
        if self.keypress_timer.isActive():
            self.keypress_timer.stop()
        self.keypress_timer.start()
        self.solveButton.setEnabled(self.captchaSolution.text()!="")

    def reject(self):
        if self.__current_jib:
            self.parent().client.skip(self.__current_jib)
            self.__current_jib = None
        if self.counter_timer.isActive():
            self.counter_timer.stop()
        QtGui.QDialog.reject(self)

    def on_timer_timeout(self):
        self.counter -= 1
        if not self.counter:
            self.reject()
            return

        if self.counter <= 10:
            self.timeoutLabel.setText(
                "<font color=\"red\">%s</font>" % self.counter
            )
        else:
            self.timeoutLabel.setText(str(self.counter))

    def on_keypress_timer_timeout(self):
        if not self.counter_timer.isActive():
            self.counter_timer.start()
