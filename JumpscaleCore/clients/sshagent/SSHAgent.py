from Jumpscale import j
from Jumpscale.core.InstallTools import Tools

import os
import sys

Tools = j.core.tools
MyEnv = j.core.myenv


class SSHAgent(j.baseclasses.object):

    __jslocation__ = "j.clients.sshagent"

    def _init(self, **kwargs):

        if MyEnv.sshagent:

            self._default_key = None

            self.ssh_socket_path = MyEnv.sshagent.ssh_socket_path
            self.available = MyEnv.sshagent.available
            self.key_names = MyEnv.sshagent.key_names
            self.key_paths = MyEnv.sshagent.key_paths
            self.key_default_name = MyEnv.sshagent.key_default_name

        else:
            raise j.exceptions.Base("cannot use sshagent, maybe not initted?")

    def profile_js_configure(self):
        return MyEnv.sshagent.profile_js_configure()

    def start(self):
        return MyEnv.sshagent.start()

    def kill(self):
        return MyEnv.sshagent.kill()

    def keypub_path_get(self):
        return MyEnv.sshagent.keypub_path_get()

    def keys_list(self):
        return MyEnv.sshagent.keys_list()

    def key_load(self):
        return MyEnv.sshagent.key_load()

    @property
    def key_default(self):
        """
        see if we can find the default sshkey using sshagent

        j.clients.sshagent.key_default

        :return: j.clients.sshkey.new() ...
        :rtype: sshkey object or None
        """
        if not self._default_key:
            name = self.key_default_name
            if j.clients.sshkey.exists(name):
                self._default_key = j.clients.sshkey.get(name)
                return self._default_key
            path = "%s/.ssh/%s" % (j.core.myenv.config["DIR_HOME"], name)
            k = j.clients.sshkey.new(name, path=path)
            self._default_key = k

        return self._default_key

    # def keys_pub_get(self):
    #     """
    #
    #     :return: [(pre,key,user)] pre e.g. ssh-rsa , user e.g. info@kkk.com
    #     """
    #     rc, out, err = j.core.tools.execute("ssh-add -L")
    #     res = []
    #     for line in out.split("\n"):
    #         if line.strip() == "":
    #             continue
    #         line = line.strip()
    #         pre, key, user = line.split(" ")
    #         res.append((pre, key, user))
    #     return res
    #
    # def key_pub_get(self, keyname=None):
    #     """
    #     Returns Content of public key that is loaded in the agent
    #
    #     :param keyname: name of key loaded to agent to get content from, if not specified is default
    #     :type keyname: str
    #     :raises RuntimeError: Key not found with given keyname
    #     :return: Content of public key
    #     :rtype: str
    #     """
    #     if not keyname:
    #         keyname = j.core.myenv.config["SSH_KEY_DEFAULT"].strip()
    #     rc, out, err = j.core.tools.execute("ssh-add -L")
    #     for line in out.split("\n"):
    #         if line.strip() == "":
    #             continue
    #         if keyname:
    #             if line.endswith(keyname):
    #                 return line
    #
    #     raise j.exceptions.Base("did not find public key")

    #
    # def _paramiko_keys_get(self):
    #     import paramiko.agent
    #
    #     a = paramiko.agent.Agent()
    #     return [key for key in a.get_keys()]
    #
    # def _paramiko_key_get(self, keyname=None):
    #     if not keyname:
    #         keyname = j.core.myenv.sshagent.key_default_name
    #     for key in self._paramiko_keys_get():
    #         # ISSUE, is always the same name, there is no way how to figure out which sshkey to use?
    #         if key.name == keyname:
    #             # maybe we can get this to work using comparing of the public keys?
    #             return key
    #
    #     raise j.exceptions.Base("could not find key:%s" % keyname)

    # def sign(self, data, keyname=None, hash=True):
    #     """
    #     will sign the data with the ssh-agent loaded
    #     :param data: the data to sign
    #     :param hash, if True, will use
    #     :param keyname is the name of the key to use to sign, if not specified will be the default key
    #     :return:
    #     """
    #     if not j.data.types.bytes.check(data):
    #         data = data.encode()
    #     self._init()
    #     import hashlib
    #
    #     key = self._paramiko_key_get(keyname)
    #     data_sha1 = hashlib.sha1(data).digest()
    #     res = key.sign_ssh_data(data_sha1)
    #     if hash:
    #         m = hashlib.sha256()
    #         m.update(res)
    #         return m.digest()
    #     else:
    #         return res
    #

    def _script_get_sshload(self, keyname=None, duration=3600 * 8):
        """
        kosmos 'j.clients.sshagent._script_get_sshload()'
        :param keyname:
        :param duration:
        :return:
        """
        DURATION = duration
        if not keyname:
            PRIVKEY = j.clients.sshkey.default.privkey.strip()
        else:
            assert j.clients.sshkey.exists(keyname)
            PRIVKEY = j.clients.sshkey.get(name=keyname).privkey.strip()
        C = """
        
        set -e
        set +x
        echo "{PRIVKEY}" > /tmp/myfile
        #check sshagent loaded if not load in the right location
        if [ $(ps ax | grep ssh-agent | wc -l) -gt 1 ]
        then
            echo "[OK] SSHAGENT already loaded"
        else        
            set +ex 
            killall ssh-agent
            set -e
            rm -f /tmp/sshagent
            rm -f /tmp/sshagent_pid
            eval "$(ssh-agent -a /tmp/sshagent)"
            # echo $SSH_AGENT_PID > /tmp/sshagent_pid
            
        fi
        
        export SSH_AUTH_SOCK=/tmp/sshagent
        
        if [[ $(ssh-add -L | grep /tmp/myfile | wc -l) -gt 0 ]]
        then
            echo "[OK] SSH key already added to ssh-agent"
        else
            echo "Need to add SSH key to ssh-agent..."
            # This should prompt for your passphrase
            chmod 600 /tmp/myfile
            ssh-add -t {DURATION} /tmp/myfile
        fi
        
        rm -f /tmp/myfile   
               
        LINE='export SSH_AUTH_SOCK=/tmp/sshagent'
        FILE='/root/.profile'
        grep -qF -- "$LINE" "$FILE" || echo "$LINE" >> "$FILE" 
        FILE='/root/.bashrc'
        grep -qF -- "$LINE" "$FILE" || echo "$LINE" >> "$FILE"
        
        """
        C2 = j.core.tools.text_replace(content=j.core.tools.text_strip(C), args=locals())
        # j.sal.fs.writeFile("/tmp/sshagent_load.sh", C2)
        return C2

    def test(self):
        """
        kosmos 'j.clients.sshagent.test()'

        """

        self._log_info("sshkeys:%s" % j.clients.sshkey._children_names_get())
        if self.available:
            self._log_info("sshkeys:%s" % self.key_paths)

        # BETTER NOT TO DO BECAUSE THEN STD KEYS GONE
        # j.clients.sshagent.kill()  # goal is to kill & make sure it get's loaded automatically
        # j.clients.sshagent.start()

        j.sal.fs.createDir("/tmp/.ssh")

        # lets generate an sshkey with a passphrase
        passphrase = "12345"
        path = "/tmp/.ssh/test_key"
        skey = j.clients.sshkey.get(name="test", path=path, passphrase=passphrase)
        skey.save()

        # this will reload the key from the db
        skey_loaded = j.clients.sshkey.get(name="test")

        assert skey_loaded._data._ddict == skey._data._ddict

        skey.generate(reset=True)
        skey.load()

        assert skey.is_loaded()

        # on mac does not seem to work
        skey.unload()
        assert skey.is_loaded() is False

    # def __str__(self):
    #     return "j.clients.sshagent"
    #
    # __repr__ = __str__
