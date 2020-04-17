"""core configuration"""
__all__ = ["branch", "redis"]

from MyEnv import MyEnv

myenv = MyEnv()
if not hasattr(myenv, "code_branch"):
    myenv.code_branch = None

core = myenv


def branch(val=""):
    """
    branch for the code we use normally development or unstable
    """
    if not val:
        return myenv.code_branch
    else:
        if myenv.code_branch != val:
            myenv.code_branch = val


def redis():
    """
    start redis so it will remember our secret and other arguments
    """
    return myenv.redis._core_get()


branch.__property__ = True
