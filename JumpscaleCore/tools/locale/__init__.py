# import threading as __threading
# __LOCALIZERS = {}
# __lock = __threading.RLock()


def getlocalizer(id, path):
    from locale import Localizer

    if id in __LOCALIZERS:
        return __LOCALIZERS[id]
    else:
        return Localizer(path)
        # try:
        #     __lock.acquire()
        #     l = Localizer(path)
        #     __LOCALIZERS[id] = l
        #     return l
        # finally:
        #     __lock.release()


# DO NOT LOCK !!!!
