# -*- coding: utf-8 -*-
"""
    qtct.solvedcaptchas
    ~~~~~~~~~~~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import logging
from PySide import QtCore, QtGui
from qtct.ui.solvedcaptchas import Ui_SolvedCaptchasDialog
from qtct.utils.i18n import _

log = logging.getLogger(__name__)

COL_ID, COL_CAPTCHA, COL_SOLUTION, COL_CORRECT = range(4)
CAPTCHA_STATUS_ICONS = {
    None: QtGui.QPixmap(":/captcha_wait.svg"),
    False: QtGui.QPixmap(":/captcha_failed.svg"),
    True: QtGui.QPixmap(":/captcha_ok.svg")
}

class CaptchaImageDelegate(QtGui.QStyledItemDelegate):
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

        if height > pixmap.height():
            rest = height - pixmap.height()
            y += int(rest/2)
            if y < 1:
                y = 1

        if width > pixmap.width():
            rest = rect.width() - pixmap.width()
            x += int(rest/2)
            if x < 1:
                x = 1

        painter.drawPixmap(x, y, width, height, pixmap)


    def sizeHint(self, option, index):
        return index.data().size()

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
#        if height > 60:
#            rest = height - 60
#            y += int(rest/2)
#            if y < 1:
#                y = 1
#
#        if width > 60:
#            rest = rect.width() - 60
#            x += int(rest/2)
#            if x < 1:
#                x = 1

        painter.drawPixmap(x, y, width, height, pixmap)

    def sizeHint(self, option, index):
        return QtCore.QSize(45, 45)

class SolvedCaptchasModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, 0, 4, parent)
        self.__captchas = {}

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
                return _("Correct")

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
#        self.parent().setColumnWidth(300, COL_CAPTCHA)

        ix = self.index(row, COL_SOLUTION, QtCore.QModelIndex())
        self.setData(ix, captcha.solution, QtCore.Qt.EditRole)
#        self.parent().setColumnWidth(150, COL_SOLUTION)

        ix = self.index(row, COL_CORRECT, QtCore.QModelIndex())
        self.setData(ix, CAPTCHA_STATUS_ICONS[captcha.correct], QtCore.Qt.EditRole)
#        self.parent().setColumnWidth(60, COL_CORRECT)
        return row

    def set_captcha_result(self, captcha):
        row = self.__captchas[captcha.ticket_id]
        ix = self.index(row, COL_CORRECT, QtCore.QModelIndex())
        self.setData(ix, CAPTCHA_STATUS_ICONS[captcha.correct], QtCore.Qt.EditRole)
        return row

class SolvedCaptchas(QtGui.QDialog, Ui_SolvedCaptchasDialog):

    GetCredits = QtCore.Signal()
    GotCredits = QtCore.Signal(int)
    SolvedCaptcha = QtCore.Signal(object)
    SolvedCaptchaResponse = QtCore.Signal(object)

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

        newFont = self.font()
        newFont.setPointSize(newFont.pointSize() + 3)
        self.setFont(newFont)

        newFont = self.font()
        newFont.setPointSize(newFont.pointSize() + 10)
        self.creditsLabel.setFont(newFont)

        self.model = SolvedCaptchasModel(self.solutionsTable)
        self.solutionsTable.setModel(self.model)

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

        self.parent().client.GotCredits.connect(self.GotCredits.emit)
        self.parent().client.SolvedCaptcha.connect(self.SolvedCaptcha.emit)
        self.parent().client.SolvedCaptchaResponse.connect(self.SolvedCaptchaResponse.emit)

#        self.GetCredits.connect(self.on_GetCredits)
        self.GotCredits.connect(self.on_GotCredits)
        self.SolvedCaptcha.connect(self.on_SolvedCaptcha)
        self.SolvedCaptchaResponse.connect(self.on_SolvedCaptchaResponse)


    def on_SolvedCaptcha(self, captcha):
        self.model.add_captcha(captcha)
#        self.solutionsTable.resizeColumnsToContents()
        self.solutionsTable.resizeRowsToContents()

    def on_SolvedCaptchaResponse(self, captcha):
        self.model.set_captcha_result(captcha)
#        self.solutionsTable.resizeColumnsToContents()
        self.solutionsTable.resizeRowsToContents()

    def on_GotCredits(self, credits):
        self.creditsLabel.setText(str(credits))

#    def on_GetCredits(self):
#        self.parent().client.get_credits()
