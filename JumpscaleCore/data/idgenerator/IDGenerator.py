from Jumpscale import j
import random

# import sys
import string

JSBASE = j.baseclasses.object


class IDGenerator(j.baseclasses.object):
    """
    generic provider of id's
    lives at j.data.idgenerator
    """

    __jslocation__ = "j.data.idgenerator"

    def _init(self, **kwargs):
        self._cryptogen = ""

    @property
    def cryptogen(self):
        if self._cryptogen == "":
            self._cryptogen = random.SystemRandom()
        return self._cryptogen

    def generateRandomInt(self, fromInt, toInt):
        """
        how to use:  j.data.idgenerator.generateRandomInt(0,10)
        """
        return random.randint(fromInt, toInt)

    def generateIncrID(self, incrTypeId, reset=False):
        """
        type is like agent, job, jobstep
        needs to be a unique type, can only work if application service is known
        how to use:  j.data.idgenerator.generateIncrID("agent")
        @reset if True means restart from 1
        """
        key = "incrementor_%s" % incrTypeId
        if reset:
            j.core.db.delete(key)
        return j.core.db.incr(key)

    def getID(self, incrTypeId, objectUniqueSeedInfo, reset=False):
        """
        get a unique id for an object uniquely identified
        remembers previously given id's
        """
        key = "idint_%s_%s" % (incrTypeId, objectUniqueSeedInfo)
        if j.core.db.exists(key) and reset is False:
            id = int(j.core.db.get(key))
            return id
        else:
            id = self.generateIncrID(incrTypeId)
            j.core.db.set(key, str(id))
            return id

    def generateGUID(self):
        """
        generate unique guid
        how to use:  j.data.idgenerator.generateGUID()
        """
        import uuid

        return str(uuid.uuid4())

    def generateXCharID(self, x):
        r = "1234567890abcdefghijklmnopqrstuvwxyz"
        l = len(r)
        out = ""
        for i in range(0, x):
            p = self.generateRandomInt(0, l - 1)
            out += r[p]
        return out

    def generateXByteID(self, x):
        out = bytearray()
        for i in range(0, x):
            out.append(self.generateRandomInt(0, 255))
        return out

    def generatePasswd(self, x, al=string.printable):
        l = len(al)
        out = ""
        for i in range(0, x):
            p = self.cryptogen.randrange(0, l - 1)
            out += al[p]
        return out

    def generateCapnpID(self):
        """
        Generates a valid id for a capnp schema.
        """
        # the bitwise is for validating the id check capnp/parser.c++
        return hex(random.randint(0, 2 ** 64) | 1 << 63)
