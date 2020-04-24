import os
import sys

dpath = os.path.dirname(__file__)
if dpath not in sys.path:
    sys.path.append(dpath)


os.environ["LC_ALL"] = "en_US.UTF-8"

from MyEnv import MyEnv


myenv = MyEnv()
