def brew(remove=False):
    """
    install brew on your local node  (can remove using the remove flag)
    """
    raise RuntimeError("implement")
    cmd = 'CI=1 /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'


def python(remove=False):
    """
    will make sure brew or other necessary parts are installed and then install python which required components we need
    """
    raise RuntimeError("implement")


def chrome(remove=False, start=True):
    """
    install chrome and run in non protected mode, so we can go to local https which is otherwise not possible
    """
    cmd = "brew cask install chromium"
    raise RuntimeError("implement")
