from Jumpscale import j

file_path = j.sal.fs.joinPaths(j.sal.fs.getDirName(__file__), "result")


class Package(j.baseclasses.threebot_package):
    def _init(self, **kwargs):
        pass

    def prepare(self):
        msg = "preparing package\n"
        j.sal.fs.writeFile(filename=file_path, contents=msg, append=True)

    def start(self):
        msg = "starting package\n"
        j.sal.fs.writeFile(filename=file_path, contents=msg, append=True)

    def stop(self):
        msg = "stopping package\n"
        j.sal.fs.writeFile(filename=file_path, contents=msg, append=True)

    def uninstall(self):
        msg = "uninstalling package\n"
        j.sal.fs.writeFile(filename=file_path, contents=msg, append=True)
