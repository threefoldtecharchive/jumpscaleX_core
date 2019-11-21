from Jumpscale import j
import copy


SCHEMA_ALERT = """
@url = jumpscale.alerthandler.alert
severity=0 (I)
status="closed,new,open" (E)
time="" (I)
environment** = "" (S)
service = "" (S)
resource = "" (S)
event = "" (S)
value** = "" (S)
messageType = "error,info,warn" (E)
text = "" (S)
count = 1 (I)
occurrences = (LI)
"""


class AlertHandler(j.baseclasses.object):
    """alert handler uses error handler (which give a logdict)
       and adding every occurrence of this errors to bcdb

    for error handling/logging docs, see jumpscaleX_core/docs/Internals/logging_errorhandling

    logdict format:

    filepath = fname     #path of the file where the log came from
    linenr = linenr
    processid =          #the process id if known
    message = msg
    public = msg         #optional public message
    level = level        #10-50
    context =            #e.g. name of a definition or class
    cat =                #a freely chosen category can be in dot notation e.g. performance.cpu.high
    data =               #data can be attached to a log e.g. a data object
    tbline =
    traceback = [tbline1,tbline2]        #list of traceback elements



    ## log (error) levels

    - CRITICAL 	50
    - ERROR 	40
    - WARNING 	30
    - INFO 	    20
    - STDOUT 	15
    - DEBUG 	10
    """

    __jslocation__ = "j.tools.alerthandler"

    def _init(self, **kwargs):
        self.model = j.data.bcdb.system.model_get(schema=SCHEMA_ALERT)

    def setup(self):
        if self.handle not in j.errorhandler.handlers:
            j.errorhandler.handlers.append(self.handle)

    def to_alert(self, logdict):
        """convert logdict to an alert

        :param logdict: logging dict (see jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md for keys)
        :type logdict: dict
        :return: object
        :rtype: jumpscale.alerthandler.alert
        """
        filepath, linenr = logdict["filepath"], logdict["linenr"]

        value = "\n".join(
            [
                logdict["context"],
                f"{filepath}:{linenr}",
                logdict["message"],
                j.core.tools.traceback_format(logdict["traceback"]),
            ]
        )

        alert = self.model.new()
        alert.severity = logdict["level"]
        alert.status = "new"
        alert.time = j.data.time.epoch
        alert.environment = "staging" if j.application.debug else "production"
        alert.service = "jsx"
        alert.resource = "kosmos"
        alert.event = "n/a"
        alert.value = value
        alert.messageType = "error"
        alert.text = logdict["message"]
        return alert

    def get_original(self, alert):
        """get original if an alert given is a duplicate

        :param alert: alert
        :type alert: jumpscale.errorhandler.alert
        :return: original alert
        :rtype: object
        """
        # For now, only indexing value
        res = self.model.find(value=alert.value)
        if res:
            return res[0]

    def add_occurrence(self, alert):
        """add an occurrence to alert history

        :param alert: alert
        :type alert: jumpscale.alerthandler.alert
        """
        alert.count += 1
        alert.occurrences.append(j.data.time.epoch)
        if alert.status == "closed":
            # reopen alert
            alert.status = "open"

    def handle(self, logdict):
        """handle error

        :param logdict: logging dict (see jumpscaleX_core/docs/Internals/logging_errorhandling/logdict.md for keys)
        :type logdict: dict
        """
        alert = self.to_alert(logdict)
        original_alert = self.get_original(alert)

        if original_alert:
            self.add_occurrence(original_alert)
            original_alert.save()
        else:
            alert.save()
