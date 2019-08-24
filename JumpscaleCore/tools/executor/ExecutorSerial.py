from Jumpscale import j

JSBASE = j.baseclasses.object

from .ExecutorBase import *
import serial


class ExecutorSerial(ExecutorBase):
    """
    This executor is primary made to communicate with devices (routers, switch, ...) over
    console cable but you can use underlaying method to communicate with any serial device.

    Please note that default mode attempt to recognize a device with cisco like commands.
    """

    def __init__(self, device, baudrate=9600, type="serial", parity="N", stopbits=1, bytesize=8, timeout=1):
        ExecutorBase.__init__(self, checkok=False)
        self.device = device
        self.baudrate = baudrate
        self.type = type
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout

        self._id = None

        self._log_info("Initialized")

        self.reconnect()
        self.fetch()

    def reconnect(self):
        self.console = serial.Serial(
            port=self.device,
            baudrate=self.baudrate,
            parity=self.parity,
            stopbits=self.stopbits,
            bytesize=self.bytesize,
            timeout=self.timeout,
        )

        return True

    @property
    def id(self):
        if self._id is None:
            self._id = "serial.%s" % (self.device)
        return self._id

    def execute(self, cmds, die=True, checkok=None, showout=True, timeout=0, env={}):
        self._log_debug("Serial command: %s" % cmds)

        if not cmds.endswith("\n"):
            cmds += "\n"

        self.send(cmds)

        return 0, "", ""

    def send(self, data):
        self.console.write(data.encode("utf-8"))

    def fetch(self):
        input = self.console.read_all()
        return input.decode("utf-8")

    def enter(self, command):
        self.send(command)
        self.send("\n")

    def _execute_script(self, content="", die=True, showout=True, checkok=None):
        raise j.exceptions.NotImplemented()

    def upload(self, source, dest, dest_prefix="", recursive=True, createdir=True):
        raise j.exceptions.NotImplemented()

    def download(self, source, dest, source_prefix="", recursive=True):
        raise j.exceptions.NotImplemented()

    def __repr__(self):
        return "Executor serial: %s" % (self.device)

    __str__ = __repr__
