class MyClass:
    def __init__(self):
        self.name = "{{name}}"
        self.dir = "{{j.dirs.HOSTDIR}}"
        self.time_created = {{j.data.time.epoch}}

    def hello(self):
        print(self.__dict__)
