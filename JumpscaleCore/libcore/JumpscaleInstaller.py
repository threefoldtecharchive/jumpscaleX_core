from MyEnv import MyEnv
from BaseInstaller import BaseInstaller
from Tools import Tools
import os
import time
import sys

myenv = MyEnv()


class JumpscaleInstaller:
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

        myenv.check_platform()

        # will check if there's already a key loaded (forwarded) will continue installation with it

        pips_level = 3

        BaseInstaller.install(sandboxed=sandboxed, force=force, branch=branch, pips_level=pips_level)

        Tools.file_touch(os.path.join(myenv.config["DIR_BASE"], "lib/jumpscale/__init__.py"))

        self.repos_get(pull=gitpull, branch=branch, reset=code_update_force)
        self.repos_link()
        self.cmds_link()

        if jsinit or not Tools.exists(os.path.join(myenv.config["DIR_BASE"], "lib/jumpscale/jumpscale_generated.py")):
            Tools.execute("cd {DIR_BASE};source env.sh;js_init generate", interactive=False, die_if_args_left=True)

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
        Tools.execute(script, die_if_args_left=True)

        # NOW JSX CAN BE USED (basic install done)

        if reset:
            Tools.execute("source /sandbox/env.sh;bcdb delete --all -f")

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
            Tools.execute(C, die=True, interactive=True, jumpscale=True)

        if threebot:
            self.threebot_init(stop=True)

    def threebot_init(self, stop=False):
        print("START THREEBOT, can take upto 3-4 min for the first time")
        # build all dependencies
        Tools.execute_jumpscale("j.servers.threebot.install()")
        # now start to see we have all
        Tools.execute_jumpscale("j.servers.threebot.start(background=True)")
        timestop = time.time() + 240.0
        ok = False
        while ok == False and time.time() < timestop:
            try:
                Tools.execute_jumpscale("assert j.core.db.get('threebot.started') == b'1'")
                ok = True
                break
            except:
                print(" - threebot starting")
                time.sleep(1)
        if not ok:
            raise Tools.exceptions.Base("could not stop threebot after install")
        print(" - Threebot Started")
        if stop:
            Tools.execute("j.servers.threebot.default.stop()", die=False, jumpscale=True, showout=False)
            time.sleep(2)
            Tools.execute("j.servers.threebot.default.stop()", die=True, jumpscale=True)
            print(" - Threebot stopped")

    def remove_old_parts(self):
        tofind = ["DigitalMe", "Jumpscale", "ZeroRobot"]
        for part in sys.path:
            if Tools.exists(part) and os.path.isdir(part):
                # print(" - REMOVE OLD PARTS:%s" % part)
                for item in os.listdir(part):
                    for item_tofind in tofind:
                        toremove = os.path.join(part, item)
                        if (
                            item.find(item_tofind) != -1
                            and toremove.find("sandbox") == -1
                            and toremove.find("github") == -1
                        ):
                            Tools.log("found old jumpscale item to remove:%s" % toremove)
                            Tools.delete(toremove)
                        if item.find(".pth") != -1:
                            out = ""
                            for line in Tools.file_text_read(toremove).split("\n"):
                                if line.find("threefoldtech") == -1:
                                    out += "%s\n" % line
                            try:
                                Tools.file_write(toremove, out)
                            except:
                                pass
                            # Tools.shell()
        tofind = ["js_", "js9"]
        for part in os.environ["PATH"].split(":"):
            if Tools.exists(part):
                for item in os.listdir(part):
                    for item_tofind in tofind:
                        toremove = os.path.join(part, item)
                        if (
                            item.startswith(item_tofind)
                            and toremove.find("sandbox") == -1
                            and toremove.find("github") == -1
                        ):
                            Tools.log("found old jumpscale item to remove:%s" % toremove)
                            Tools.delete(toremove)

    # def prebuilt_copy(self):
    #     """
    #     copy the prebuilt files to the {DIR_BASE} location
    #     :return:
    #     """
    #     self.cmds_link(generate_js=False)
    #     # why don't we use our primitives here?
    #     Tools.execute("cp -a {DIR_CODE}/github/threefoldtech/sandbox_threebot_linux64/* /")
    #     # -a won't copy hidden files
    #     Tools.execute("cp {DIR_CODE}/github/threefoldtech/sandbox_threebot_linux64/.startup.toml /")
    #     Tools.execute("source {DIR_BASE}/env.sh; kosmos 'j.data.nacl.configure(generate=True,interactive=False)'")
    #
    def repos_get(self, pull=False, prebuilt=False, branch=None, reset=False):
        assert not prebuilt  # not supported yet
        if prebuilt:
            raise Tools.exceptions.Base("not implemented")
            # myenv.GITREPOS["prebuilt"] = PREBUILT_REPO

        done = []

        for NAME, d in myenv.GITREPOS.items():
            GITURL, BRANCH, RPATH, DEST = d
            if GITURL in done:
                continue

            if branch:
                # dont understand this code, looks bad TODO:
                C = f"""git ls-remote --heads {GITURL} {branch}"""
                _, out, _ = Tools.execute(C, showout=False, die_if_args_left=True, interactive=False)
                if out:
                    BRANCH = branch

            try:
                dest = Tools.code_github_get(url=GITURL, rpath=RPATH, branch=BRANCH, pull=pull, reset=reset)
            except Exception as e:
                r = Tools.code_git_rewrite_url(url=GITURL, ssh=False)
                Tools.code_github_get(url=GITURL, rpath=RPATH, branch=BRANCH, pull=pull, reset=reset)

            done.append(GITURL)

        if prebuilt:
            self.prebuilt_copy()

    def repos_link(self):
        """
        link the jumpscale repo's to right location in sandbox
        :return:
        """

        for NAME, d in myenv.GITREPOS.items():
            GITURL, BRANCH, PATH, DEST = d

            (host, type, account, repo, url2, branch2, GITPATH, RPATH, port) = Tools.code_giturl_parse(url=GITURL)
            srcpath = "%s/%s" % (GITPATH, PATH)
            if not Tools.exists(srcpath):
                raise Tools.exceptions.Base("did not find:%s" % srcpath)

            DESTPARENT = os.path.dirname(DEST.rstrip())

            script = f"""
            set -e
            rm -f {DEST}
            mkdir -p {DESTPARENT}
            ln -s {GITPATH}/{PATH} {DEST}
            """
            Tools.execute(script, die_if_args_left=True)

    def cmds_link(self):
        _, _, _, _, loc = Tools._code_location_get(repo="jumpscaleX_core/", account="threefoldtech")
        for src in os.listdir("%s/cmds" % loc):
            src2 = os.path.join(loc, "cmds", src)
            dest = "%s/bin/%s" % (myenv.config["DIR_BASE"], src)
            if not os.path.exists(dest):
                Tools.link(src2, dest, chmod=770)
        Tools.link("%s/install/jsx.py" % loc, "{DIR_BASE}/bin/jsx", chmod=770)
