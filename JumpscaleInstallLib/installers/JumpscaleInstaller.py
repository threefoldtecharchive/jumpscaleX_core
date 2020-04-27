import os
import time
import sys


class JumpscaleInstaller:
    def __init__(self, myenv):
        self._my = myenv
        self._tools = self._my.tools

    def install(
        self,
        sandboxed=False,
        force=False,
        gitpull=False,
        branch=None,
        threebot=False,
        identity=None,
        reset=None,
        jsinit=True,
        email=None,
        words=None,
        code_update_force=False,
    ):

        self._my.check_platform()

        # will check if there's already a key loaded (forwarded) will continue installation with it

        pips_level = 3

        self._my.installers.base.install(sandboxed=sandboxed, force=force, branch=branch, pips_level=pips_level)

        self._tools.file_touch(os.path.join(self._my.config["DIR_BASE"], "lib/jumpscale/__init__.py"))

        self.repos_get(pull=gitpull, branch=branch, reset=code_update_force)
        self.repos_link()
        self.cmds_link()

        if jsinit or not self._tools.exists(
            os.path.join(self._my.config["DIR_BASE"], "lib/jumpscale/jumpscale_generated.py")
        ):
            self._tools.execute(
                "cd {DIR_BASE};source env.sh;js_init generate", interactive=False, die_if_args_left=True
            )

        script = """
        set -e
        cd {DIR_BASE}
        source env.sh
        mkdir -p {DIR_BASE}/openresty/nginx/logs
        mkdir -p {DIR_BASE}/var/log
        # kosmos 'j.data.nacl.configure(generate=True,interactive=False)'
        # kosmos 'j.core.installer_jumpscale.remove_old_parts()'
        # kosmos --instruct=/tmp/instructions.toml
        # kosmos 'j.core.tools.pprint("JumpscaleX init step for encryption OK.")'
        """
        self._tools.execute(script, die_if_args_left=True)

        # NOW JSX CAN BE USED (basic install done)

        if reset:
            self._tools.execute("source /sandbox/env.sh;bcdb delete --all -f")

        if True or identity or threebot:

            if not identity:
                identity = ""
            if not email:
                email = ""
            if not words:
                words = ""
            C = f"""
            j.me.configure(tname='{identity}',ask=False, email='{email}',words='{words}')
            """
            self._tools.execute(C, die=True, interactive=True, jumpscale=True)

        if threebot:
            self.threebot_init(stop=True)

    def threebot_init(self, stop=False):
        print("START THREEBOT, can take upto 3-4 min for the first time")
        # build all dependencies
        self._tools.execute_jumpscale("j.servers.threebot.install()")
        # now start to see we have all
        self._tools.execute_jumpscale("j.servers.threebot.start(background=True)")
        timestop = time.time() + 240.0
        ok = False
        while ok == False and time.time() < timestop:
            try:
                self._tools.execute_jumpscale("assert j.core.db.get('threebot.started') == b'1'")
                ok = True
                break
            except:
                print(" - threebot starting")
                time.sleep(1)
        if not ok:
            raise self._tools.exceptions.Base("could not stop threebot after install")
        print(" - Threebot Started")
        if stop:
            self._tools.execute("j.servers.threebot.default.stop()", die=False, jumpscale=True, showout=False)
            time.sleep(2)
            self._tools.execute("j.servers.threebot.default.stop()", die=True, jumpscale=True)
            print(" - Threebot stopped")

    def remove_old_parts(self):
        tofind = ["DigitalMe", "Jumpscale", "ZeroRobot"]
        for part in sys.path:
            if self._tools.exists(part) and os.path.isdir(part):
                # print(" - REMOVE OLD PARTS:%s" % part)
                for item in os.listdir(part):
                    for item_tofind in tofind:
                        toremove = os.path.join(part, item)
                        if (
                            item.find(item_tofind) != -1
                            and toremove.find("sandbox") == -1
                            and toremove.find("github") == -1
                        ):
                            self._tools.log("found old jumpscale item to remove:%s" % toremove)
                            self._tools.delete(toremove)
                        if item.find(".pth") != -1:
                            out = ""
                            for line in self._tools.file_text_read(toremove).split("\n"):
                                if line.find("threefoldtech") == -1:
                                    out += "%s\n" % line
                            try:
                                self._tools.file_write(toremove, out)
                            except:
                                pass
                            # self._tools.shell()
        tofind = ["js_", "js9"]
        for part in os.environ["PATH"].split(":"):
            if self._tools.exists(part):
                for item in os.listdir(part):
                    for item_tofind in tofind:
                        toremove = os.path.join(part, item)
                        if (
                            item.startswith(item_tofind)
                            and toremove.find("sandbox") == -1
                            and toremove.find("github") == -1
                        ):
                            self._tools.log("found old jumpscale item to remove:%s" % toremove)
                            self._tools.delete(toremove)

    # def prebuilt_copy(self):
    #     """
    #     copy the prebuilt files to the {DIR_BASE} location
    #     :return:
    #     """
    #     self.cmds_link(generate_js=False)
    #     # why don't we use our primitives here?
    #     self._tools.execute("cp -a {DIR_CODE}/github/threefoldtech/sandbox_threebot_linux64/* /")
    #     # -a won't copy hidden files
    #     self._tools.execute("cp {DIR_CODE}/github/threefoldtech/sandbox_threebot_linux64/.startup.toml /")
    #     self._tools.execute("source {DIR_BASE}/env.sh; kosmos 'j.data.nacl.configure(generate=True,interactive=False)'")
    #
    def repos_get(self, pull=False, prebuilt=False, branch=None, reset=False):
        assert not prebuilt  # not supported yet
        if prebuilt:
            raise self._tools.exceptions.Base("not implemented")
            # self._my.GITREPOS["prebuilt"] = PREBUILT_REPO

        done = []

        for NAME, d in self._my.GITREPOS.items():
            GITURL, BRANCH, RPATH, DEST = d
            if GITURL in done:
                continue

            if branch:
                # dont understand this code, looks bad TODO:
                C = f"""git ls-remote --heads {GITURL} {branch}"""
                _, out, _ = self._tools.execute(C, showout=False, die_if_args_left=True, interactive=False)
                if out:
                    BRANCH = branch

            try:
                dest = self._tools.code_github_get(url=GITURL, rpath=RPATH, branch=BRANCH, pull=pull, reset=reset)
            except Exception as e:
                r = self._tools.code_git_rewrite_url(url=GITURL, ssh=False)
                self._tools.code_github_get(url=GITURL, rpath=RPATH, branch=BRANCH, pull=pull, reset=reset)

            done.append(GITURL)

        if prebuilt:
            self.prebuilt_copy()

    def repos_link(self):
        """
        link the jumpscale repo's to right location in sandbox
        :return:
        """

        for NAME, d in self._my.GITREPOS.items():
            GITURL, BRANCH, PATH, DEST = d

            (host, type, account, repo, url2, branch2, GITPATH, RPATH, port) = self._tools.code_giturl_parse(url=GITURL)
            srcpath = "%s/%s" % (GITPATH, PATH)
            if not self._tools.exists(srcpath):
                raise self._tools.exceptions.Base("did not find:%s" % srcpath)

            DESTPARENT = os.path.dirname(DEST.rstrip())

            script = f"""
            set -e
            rm -f {DEST}
            mkdir -p {DESTPARENT}
            ln -s {GITPATH}/{PATH} {DEST}
            """
            self._tools.execute(script, die_if_args_left=True)

    def cmds_link(self):
        _, _, _, _, loc = self._tools._code_location_get(repo="jumpscaleX_core/", account="threefoldtech")
        for src in os.listdir("%s/cmds" % loc):
            src2 = os.path.join(loc, "cmds", src)
            dest = "%s/bin/%s" % (self._my.config["DIR_BASE"], src)
            if not os.path.exists(dest):
                self._tools.link(src2, dest, chmod=770)
        self._tools.link("%s/install/jsx.py" % loc, "{DIR_BASE}/bin/jsx", chmod=770)
