from Jumpscale import j

d = j.baseclasses.dict()


class something:
    def __init__(self):
        self.a = "1"


d["a"] = something()
d["b"] = something()

# d["a"] = 1
# d["b"] = 2

j.shell()
