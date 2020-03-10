""" Timestamp routines """

import time
import traceback

LASTTIME = 0
DELTATIME_INITIALIZED = False


class TimeInterval:
    """ Enumerator for time interval units """

    NANOSECONDS = -3
    MICROSECONDS = -2
    MILLISECONDS = -1
    SECONDS = 0
    MINUTES = 1
    HOURS = 2
    DAYS = 3
    WEEKS = 4
    MONTHS = 5
    YEARS = 6

    __jslocation__ = "j.data.timeinterval"


def printdelta():
    """
    This is a function for source code or performance debugging.
    Call this function at every point cut in the source code
    where you want to print out a timestamp, together with the source code line
    """

    global LASTTIME, DELTATIME_INITIALIZED
    currenttime = time.time()
    if DELTATIME_INITIALIZED:
        print(("... TIME DELTA: " + str(currenttime - LASTTIME)))
        LASTTIME = currenttime
    else:
        print("... STARTING TIME MEASUREMENTS")
        LASTTIME = currenttime
        DELTATIME_INITIALIZED = True
    print(
        (
            " @ Source file ["
            + traceback.extract_stack()[-2][0]
            + "] line ["
            + str(traceback.extract_stack()[-2][1])
            + "]"
        )
    )


def getabstime():
    """ Get string representation of absolute time in milliseconds """
    x = time.time()
    part1 = time.strftime("%a %d %b %Y, %H:%M:%S", time.localtime(x))
    part2 = ".%03d" % ((x % 1) * 1000)
    return part1 + part2
