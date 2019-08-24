from path import Path
from Jumpscale import j

JSBASE = j.baseclasses.object


class PathFactory(j.baseclasses.object):
    def __init__(self):
        if not hasattr(self, "__jslocation__"):
            self.__jslocation__ = "j.tools.path"
        JSBASE.__init__(self)

    def get(self, startpath):
        """
        example1:
        ```
        d = j.tools.path.get("/tmp")
        for i in d.walk():
            if i.isfile():
                if i.name.startswith("something_"):
                    i.remove()
        ```

        other:
        files = d.walkfiles("*.pyc")
        num_files = len(d.files())
        """
        return Path(startpath)
