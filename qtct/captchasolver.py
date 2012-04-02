# -*- coding: utf-8 -*-
"""
    qtct.solver
    ~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import logging
from PySide import QtCore, QtGui
from qtct.ui.captchasolve import Ui_CaptchaSolverDialog

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

#    @QtCore.Slot(int, QtGui.QImage)
    def on_client_NewCaptcha(self, captchaticket):
        self.captchaSolution.setText("")
        self.__current_jib = captchaticket.ticket_id
        self.captchaLabel.setPixmap(QtGui.QPixmap.fromImage(captchaticket.image))
        self.resize(10, 10)
        self.adjustSize()
        self.show()


    def accept(self):
        if self.__current_jib:
            log.info("Submitting captcha solution %r for ticket it %s",
                     self.captchaSolution.text(), self.__current_jib)
            self.parent().client.answer(
                self.__current_jib, self.captchaSolution.text()
            )
            self.__current_jib = None
        QtGui.QDialog.accept(self)

    def reject(self):
        if self.__current_jib:
            self.parent().client.skip(self.__current_jib)
            self.__current_jib = None
        QtGui.QDialog.reject(self)
