# -*- coding: utf-8 -*-
"""
    qtct.api.client
    ~~~~~~~~~~~~~~~

    :copyright: © 2012 UfSoft.org - :email:`Pedro Algarvio (pedro@algarvio.me)`
    :license: BSD, see LICENSE for more details.
"""

import json
import logging
from functools import partial
from PySide import QtCore, QtNetwork, QtGui

from qtct import __package_name__, __version__
from qtct.utils.i18n import _

log = logging.getLogger(__name__)

(REQ_TYPE_CREDITS, REQ_TYPE_ENQUEUE, REQ_TYPE_DEQUEUE, REQ_TYPE_WAITTIME,
 REQ_TYPE_ANSWER, REQ_TYPE_SOLUTION, REQ_TYPE_AUTH) = range(7)

(STATE_STOPPED, STATE_STOPPING, STATE_STARTING,
 STATE_RUNNING, STATE_ENQUEUED, STATE_ANSWERING) = range(6)

class CaptchaTicket(QtCore.QObject):
    def __init__(self, parent, ticket_id, image):
        QtCore.QObject.__init__(self, parent)
        self.ticket_id = ticket_id
        self.image = image
        self.solution = None
        self.correct = None

    def set_solution(self, solution):
        self.solution = solution

    def set_solution_result(self, result):
        self.correct = result

    def solutionAvailable(self):
        return self.correct is not None

    def wasSkipped(self):
        return self.solution == ""

    def wasSolved(self):
        return self.solution is not None

    def __repr__(self):
        return '<%s ticket-id=%s solution=%r skipped=%r correct=%r>' % (
            self.__class__.__name__, self.ticket_id, self.solution,
            self.solution == "", self.correct
        )


class CaptchaTrader(QtCore.QObject):

    API_KEY = "2b48926b1336431cfb2b59832d5a1fca"
    API_URL = "http://api.captchatrader.com"


    __GetCredits = QtCore.Signal()
    __GotCredits = QtCore.Signal(str)
    __GetWaitTime = QtCore.Signal()
    __GotWaitTime = QtCore.Signal(str)
    __Answer = QtCore.Signal(int, str)
    __Answered = QtCore.Signal(int, str, str)
    __Dequeue = QtCore.Signal()
    __Dequeued = QtCore.Signal(str)
    __Enqueue = QtCore.Signal()
    __Enqueued = QtCore.Signal(str)
    __GetSolution = QtCore.Signal()
    __GotSolution = QtCore.Signal(str)

    Exited = QtCore.Signal()
    GotCredits = QtCore.Signal(int)

    StateChanged = QtCore.Signal(int, int)
    __StateChanged = QtCore.Signal(int, int)

    GotWaitTime = QtCore.Signal(int, int)

    NewCaptcha = QtCore.Signal(object)
    SolvedCaptcha = QtCore.Signal(object)
    SolvedCaptchaResponse = QtCore.Signal(object)

    ERRORS = {
        "INTERNAL ERROR": _("The server encountered an unexpected situation "
                            "and the request was aborted."),
        "INVALID PARAMETERS": _("The request was not submitted correctly."),
        "INVALID USER": _("The username/password combination was incorrect."),
        "CONNECTION LIMIT": _("The user has exceeded the number of connections "
                              "permitted. A normal response is to try again "
                              "later and dequeue existing connections."),
        "RATE LIMIT": _("The maximum request rate (configured on the account "
                        "page) has been exceeded."),
        "SUBMIT LIMIT": _("The maximum hourly submission rate (configured on "
                          "the account page) has been exceeded.")
    }



    def __init__(self, parent=None, username=None, password=None):
        QtCore.QObject.__init__(self, parent)
        self.username = username
        self.password = password
        self.credits = 0

        self.manager = QtNetwork.QNetworkAccessManager(self)
        self.manager.finished[QtNetwork.QNetworkReply].connect(self.__on_reply)

        self.__replies = set()
        self.__state = STATE_STOPPED
        self.__exiting = False
        self.__cookie_value = None
        self.__tickets = {}
        self.__answer_waiting = []

        # Connect signals to slots
        self.__Answer.connect(self.__on_Answer)
        self.__Answered.connect(self.__on_Answered)
        self.__Enqueue.connect(self.__on_Enqueue)
        self.__Enqueued.connect(self.__on_Enqueued)
        self.__Dequeue.connect(self.__on_Dequeue)
        self.__Dequeued.connect(self.__on_Dequeued)
        self.__GetCredits.connect(self.__on_GetCredits)
        self.__GotCredits.connect(self.__on_GotCredits)
        self.__GetWaitTime.connect(self.__on_GetWaitTime)
        self.__GotWaitTime.connect(self.__on_GotWaitTime)
        self.__StateChanged.connect(self.__on_StateChanged)
        self.__GetSolution.connect(self.__on_GetSolution)
        self.__GotSolution.connect(self.__on_GotSolution)


    #===========================================================================
    # State Handling
    def start(self):
        self.__StateChanged.emit(self.__state, STATE_STARTING)

    def stop(self):
        self.__StateChanged.emit(self.__state, STATE_STOPPING)

    def quit(self):
        log.info("Exit client!")
        self.__exiting = True
        self.stop()

    def isRunning(self):
        return self.__state >= STATE_RUNNING

    def __on_StateChanged(self, prev, state):
        st = {
            0: "STATE_STOPPED",
            1: "STATE_STOPPING",
            2: "STATE_STARTING",
            3: "STATE_RUNNING",
            4: "STATE_ENQUEUED",
            5: "STATE_ANSWERING"
        }
        log.info("State is changing: %s => %s", st[prev], st[state])
        if state == STATE_STOPPED:
            log.info("CaptchaTrader client stopped. Exiting: %s", self.__exiting)
            if self.__exiting:
                self.Exited.emit()
        elif state == STATE_STOPPING:
            if prev == STATE_ENQUEUED:
                self.dequeue()
            else:
                def delayed():
                    self.__StateChanged.emit(state, STATE_STOPPED)
                QtCore.QTimer.singleShot(50, delayed)

        elif state == STATE_STARTING:
            QtCore.QTimer.singleShot(50, self.__authenticate)
            if prev == STATE_STOPPED:
                def delayed():
                    self.__StateChanged.emit(state, STATE_RUNNING)
                QtCore.QTimer.singleShot(50, delayed)
        elif state == STATE_RUNNING:
            if prev in (STATE_ANSWERING, STATE_RUNNING, STATE_STARTING):
                QtCore.QTimer.singleShot(100, self.get_credits)
                QtCore.QTimer.singleShot(150, self.enqueue)
        elif state == STATE_ENQUEUED:
            QtCore.QTimer.singleShot(50, self.get_wait_time)
        elif state == STATE_ANSWERING:
            pass
        # Store and propagate signal
        self.StateChanged.emit(self.__state, state)
        self.__state = state
        log.info("State changed to %s", st[state])
    # State Handling
    #===========================================================================


    #===========================================================================
    # Get Credits
    def get_credits(self):
        self.__GetCredits.emit()

    @QtCore.Slot()
    def __on_GetCredits(self):
        if REQ_TYPE_CREDITS in self.__replies:
            log.info("Not requesting credits again. Wait until last credits "
                     "request has finished...")
            return

        log.info("Loading credits")
        reply = self.__send_request("get_credits")
        reply.error[QtNetwork.QNetworkReply.NetworkError].connect(self.__on_error)
        reply.req_type = REQ_TYPE_CREDITS
        self.__replies.add(REQ_TYPE_CREDITS)

    def __on_GotCredits(self, data):
        self.__replies.remove(REQ_TYPE_CREDITS)
        status, credits_or_error = json.loads(data)
        if status < 0:
            error = self.ERRORS.get(credits_or_error, credits_or_error)
            log.error("Failed to load credits: %s", error)
        else:
            self.credits = credits_or_error
            log.info("Credits available: %s", credits_or_error)
            self.GotCredits.emit(credits_or_error)
    # Get Credits
    #===========================================================================

    #===========================================================================
    # Enqueue
    def enqueue(self):
        self.__Enqueue.emit()

    def __on_Enqueue(self):
        if REQ_TYPE_ENQUEUE in self.__replies:
            log.info("Not enqueueing again. Wait until last request has finished")
            return
        elif self.__state >= STATE_ENQUEUED:
            return

        log.info("Enqueue'ing")
        reply = self.__send_request("enqueue")
        reply.error[QtNetwork.QNetworkReply.NetworkError].connect(self.__on_error)
        reply.req_type = REQ_TYPE_ENQUEUE
        self.__replies.add(REQ_TYPE_ENQUEUE)
        QtCore.QTimer.singleShot(
            500, partial(self.__StateChanged.emit, self.__state, STATE_ENQUEUED)
        )

    def __on_Enqueued(self, data):
        self.__replies.remove(REQ_TYPE_ENQUEUE)
        log.info("Enqueued")
        try:
            ticket, image_data = json.loads(data)
        except Exception, err:
            log.exception(err)
            self.__StateChanged.emit(self.__state, STATE_RUNNING)
        else:
            if ticket < 0:
                log.error("Failed enqueue request: %s", self.ERRORS.get(image_data, image_data))
                if image_data == "CONNECTION LIMIT":
                    QtCore.QTimer.singleShot(1000, self.dequeue)
                    QtCore.QTimer.singleShot(1500, self.enqueue)
                if image_data != "DEQUEUE":
                    self.__StateChanged.emit(self.__state, STATE_RUNNING)
                return
            image_type, image_data_b64 = image_data.encode('utf-8').split(',', 1)
            image = QtGui.QImage()
            bytearray = QtCore.QByteArray.fromBase64(image_data_b64)

            loaded = image.loadFromData(bytearray)
            if loaded is False:
                log.error("Failed to create a QImage with the provided data")
                self.__StateChanged.emit(self.__state, STATE_RUNNING)
            else:
                log.info("Got a new captcha request. Ticket ID: %s", ticket)
                self.__StateChanged.emit(self.__state, STATE_ANSWERING)
                captchaticket = CaptchaTicket(self, ticket, image)
                self.__tickets[ticket] = captchaticket
                self.NewCaptcha.emit(captchaticket)
    # Enqueue
    #===========================================================================

    #===========================================================================
    # Dequeue
    def dequeue(self):
        self.__Dequeue.emit()

    def __on_Dequeue(self):
        if REQ_TYPE_DEQUEUE in self.__replies:
            log.info("Not dequeueing again. Wait until last request has finished")
            return
        elif self.__state < STATE_ENQUEUED:
            return
        log.info("Dequeue'ing")
        reply = self.__send_request(
            "dequeue", username=self.username, password=self.password
        )
        reply.error[QtNetwork.QNetworkReply.NetworkError].connect(self.__on_error)
        reply.req_type = REQ_TYPE_DEQUEUE
        self.__replies.add(REQ_TYPE_DEQUEUE)

    def __on_Dequeued(self, data):
        self.__replies.remove(REQ_TYPE_DEQUEUE)
        try:
            data = json.loads(data)
        except Exception, err:
            log.exception(err)
        else:
            if data[0] < 0:
                error = self.ERRORS.get(data[1], data[1])
                log.error("Failed to dequeue: %s", error)
            if self.__state == STATE_STOPPING:
                self.__StateChanged.emit(self.__state, STATE_STOPPED)
            else:
                self.__StateChanged.emit(self.__state, STATE_RUNNING)
        log.debug("Dequeued...")
    # Dequeue
    #===========================================================================

    #===========================================================================
    # Get Wait Time
    def get_wait_time(self):
        self.__GetWaitTime.emit()

    def __on_GetWaitTime(self):
        if REQ_TYPE_WAITTIME in self.__replies:
            log.info("Not getting wait time again again. Wait until last request has finished")
            return
        elif self.__state > STATE_ENQUEUED:
            return
        log.info("Get Wait Time")
        reply = self.__send_request("get_wait_time")
        reply.req_type = REQ_TYPE_WAITTIME
        reply.error[QtNetwork.QNetworkReply.NetworkError].connect(self.__on_error)
        self.__replies.add(REQ_TYPE_WAITTIME)

    def __on_GotWaitTime(self, data):
        self.__replies.remove(REQ_TYPE_WAITTIME)
        log.info("Got Wait Time")
        try:
            data = json.loads(data)
        except Exception, err:
            log.exception(err)
        else:
            if data[0] < 0:
                error = self.ERRORS.get(data[1], data[1])
                log.error("Failed to get wait time: %s", error)
            elif data[0] == data[1]:
                log.error("The user is not Enqueued")
                if self.isRunning():
                    QtCore.QTimer.singleShot(0, self.enqueue)
            else:
                log.info("Queue Position: %s  Wait time: %s seconds",
                         data[1], data[2])
                self.GotWaitTime.emit(data[1], data[2])

            if self.isRunning():
                next_query = data[2]/2*1000.0
                if next_query > 5000:
                    next_query = 5000
                elif next_query < 1000:
                    next_query = 1000
                QtCore.QTimer.singleShot(next_query, self.get_wait_time)
    # Get Wait Time
    #===========================================================================

    #===========================================================================
    # Answer Captcha
    def answer(self, jid, answer):
        self.__Answer.emit(jid, answer)

    def skip(self, jid):
        self.__Answer.emit(jid, "")

    def __on_Answer(self, jid, answer):
        log.info("Submitting captcha solution %r for ticket it %s", answer, jid)
        reply = self.__send_request(
            "answer", password=self.password, username=self.username,
            ticket=jid, value=answer.encode('utf-8')
        )

        self.__tickets[jid].set_solution(answer)

        reply.error[QtNetwork.QNetworkReply.NetworkError].connect(self.__on_error)
        reply.req_type = REQ_TYPE_ANSWER
        reply.jid = jid
        reply.solution = answer
        self.__replies.add(REQ_TYPE_ANSWER)

    def __on_Answered(self, jid, solution, data):
        if REQ_TYPE_ANSWER in self.__replies:
            self.__replies.remove(REQ_TYPE_ANSWER)

        log.info("Answered")
        try:
            data = json.loads(data)
            if data[0] < 0:
                error = self.ERRORS.get(data[1], data[1])
                log.error("Failed to post answer for ticket ID %s: %s", jid, error)
                if jid in self.__tickets:
                    self.__tickets.pop(jid)
                if jid in self.__answer_waiting:
                    self.__answer_waiting.remove(jid)
            elif data[0] == 0:
                log.info("Answer for ticket ID %s posted successfully", jid)
                self.SolvedCaptcha.emit(self.__tickets[jid])
        except Exception, err:
            log.exception(err)

        if self.__state == STATE_ANSWERING:
            self.__StateChanged.emit(self.__state, STATE_RUNNING)

        QtCore.QTimer.singleShot(2500, self.get_solution)
    # Answer Captcha
    #===========================================================================

    #===========================================================================
    # Get Captcha solution
    def get_solution(self):
        self.__GetSolution.emit()

    def __on_GetSolution(self):
        if REQ_TYPE_SOLUTION in self.__replies:
            log.info("Not requesting solutions again. Wait until last request has finished...")
            return

        if self.__cookie_value is None:
            self.__authenticate()
            return

        for ticket_id, ticket in self.__tickets.iteritems():
            if ticket.solutionAvailable():
                if ticket_id in self.__answer_waiting:
                    self.__answer_waiting.remove(ticket_id)
                continue
            elif ticket.wasSkipped() or not ticket.wasSolved():
                continue
            self.__answer_waiting.append(ticket_id)

        if not self.__answer_waiting:
            return

        while True:
            try:
                ticket_id = self.__answer_waiting.pop(0)
                if not self.__tickets[ticket_id].solutionAvailable():
                    break
            except IndexError:
                ticket_id = None
                break

        if ticket_id is None:
            return

        self.__answer_waiting.append(ticket_id)

        log.info("Querying for solution regarding ticket: %s", ticket_id)

        request = QtNetwork.QNetworkRequest()
        request.setRawHeader(
            "User-Agent", "{0} {1}".format(__package_name__, __version__)
        )
        url = QtCore.QUrl(
            "{0}/get_response/{1}/{2}/".format(
                self.API_URL, self.__cookie_value, ticket_id
            )
        )
        log.trace("Solution URL: %s", url)
        request.setUrl(url)
        reply = self.manager.get(request)
        reply.error[QtNetwork.QNetworkReply.NetworkError].connect(self.__on_error)
        reply.req_type = REQ_TYPE_SOLUTION
        reply.ticket_id = ticket_id
        self.__replies.add(REQ_TYPE_SOLUTION)

    def __on_GotSolution(self, data):
        self.__replies.remove(REQ_TYPE_SOLUTION)

        try:
            data = json.loads(data)
            log.info("Got solutions: %s", data)
            if data[0] < 0:
                error = self.ERRORS.get(data[1], data[1])
                log.error("Failed get solutions: %s", error)
            elif data[0] == 0:
                log.trace("Foo: %s", data[1])
                self.GotCredits.emit(data[2])
                for jid, solved in data[1].iteritems():
                    if solved is None:
                        log.trace("Not jid %s not yet solved.", jid)
                        continue
                    log.debug("Job ID %s solved correctly: %s", jid, solved)
                    captcha = self.__tickets[int(jid)]
                    captcha.set_solution_result(solved)
                    self.SolvedCaptchaResponse.emit(captcha)
        except Exception, err:
            log.exception(err)
        QtCore.QTimer.singleShot(2500, self.get_solution)
    # Get Captcha solution
    #===========================================================================

    #===========================================================================
    # Exit
    def exit(self):
        if self.__state > STATE_STOPPING:
            self.__StateChanged.emit(self.__state, STATE_STOPPING)

    # Exit
    #===========================================================================

    def __on_reply(self, reply):
        if reply.req_type == REQ_TYPE_CREDITS:
            self.__GotCredits.emit(str(reply.readAll()))
        elif reply.req_type == REQ_TYPE_ENQUEUE:
            self.__Enqueued.emit(unicode(reply.readAll()).decode('utf-8'))
        elif reply.req_type == REQ_TYPE_DEQUEUE:
            self.__Dequeued.emit(str(reply.readAll()))
        elif reply.req_type == REQ_TYPE_WAITTIME:
            self.__GotWaitTime.emit(str(reply.readAll()))
        elif reply.req_type == REQ_TYPE_ANSWER:
            self.__Answered.emit(reply.jid, reply.solution, str(reply.readAll()))
        elif reply.req_type == REQ_TYPE_SOLUTION:
            self.__GotSolution.emit(str(reply.readAll()))
        elif reply.req_type == REQ_TYPE_AUTH:
            log.debug("Setting up the http cookiejar")
            cookiejar = self.manager.cookieJar()
            if cookiejar:
                for cookie in cookiejar.cookiesForUrl(reply.request().url()):
                    if cookie.name() == "CaptchaTrader":
                        self.__cookie_value = cookie.value()

                cookiejar.setCookiesFromUrl(
                    cookiejar.cookiesForUrl(reply.request().url()),
                    QtCore.QUrl(self.API_URL)
                )
                self.manager.setCookieJar(cookiejar)
        else:
            log.warning("!!!!!!!!!!! %s", reply)
            log.warning("%s", reply.readAll())
            # Finally, let's delete the reply
            request = reply.request()
            print 'REQUEST DETAILS:', request.url()
            try:
                print 'TYPE:', type(request.req_type), request.req_type
            except Exception:
                print
            print 'Headers:'
            for header in request.rawHeaderList():
                print "%s: %s" % (header, request.rawHeader(header))

        reply.deleteLater()

    def __on_error(self, error):
        NetworkErrors = QtNetwork.QNetworkReply.NetworkError
        if error == NetworkErrors.AuthenticationRequiredError:
            self.__authenticate()
        else:
            log.error(error)

    def __send_request(self, path, **kwargs):
        request = QtNetwork.QNetworkRequest()
        request.setRawHeader(
            "User-Agent", "{0} {1}".format(__package_name__, __version__)
        )
        log.info("Processing")
        if kwargs:
            request.setHeader(
                QtNetwork.QNetworkRequest.ContentTypeHeader,
                "application/x-www-form-urlencoded"
            )
            request.setUrl(QtCore.QUrl("{0}/{1}/".format(self.API_URL, path)))
            params = QtCore.QUrl()
            for key, value in kwargs.iteritems():
                params.addQueryItem(key, str(value))
            params.addQueryItem("api_key", self.API_KEY)
            return self.manager.post(request, params.encodedQuery())
        else:
            request.setUrl(QtCore.QUrl(
                "{0}/{1}/username:{2}/password:{3}/".format(
                    self.API_URL, path, self.username, self.password
                )
            ))
            return self.manager.get(request)


    def __authenticate(self):
        log.info("Sending authentication request")
        request = QtNetwork.QNetworkRequest()
        request.setHeader(
            QtNetwork.QNetworkRequest.ContentTypeHeader,
            "application/x-www-form-urlencoded"
        )
        request.setRawHeader(
            "User-Agent", "{0} {1}".format(__package_name__, __version__)
        )
        request.setUrl(QtCore.QUrl("http://www.captchatrader.com/login"))
        params = QtCore.QUrl()
        params.addQueryItem("data[User][username]", self.username)
        params.addQueryItem("data[User][password]", self.password)
        reply = self.manager.post(request, params.encodedQuery())
        reply.req_type = REQ_TYPE_AUTH
