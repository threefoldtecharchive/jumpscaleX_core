# 3sdk troubleshooting

is mainly for experts who already used jumpscale before


## <a name='SignatureVerification'></a>signature verification failed

- ensure your pubkey to be the same as local configured nacl

```bash

Tue 14 19:18:01 e/Jumpscale/me/Me.py - 461 - tfgrid_phonebook_register
: EXCEPTION:
    signature verification failed, ensure your pubkey to be the same as local configured nacl

--TRACEBACK------------------

```

is most likely caused that you registered on phonebook with different words other than the ones in the 3bot connect app

## case you have an old container with your old key and secret

- you can get your private key `cat /sandbox/cfg/keys/default/key.priv`
- and the secret `cat /sandbox/cfg/jumpscale_config.toml | grep SECRET`


#### Recovering old words (saved)

if you have your key.priv and secret from jumpscale_config and want to restore them


##### Restore the key

either copy the file back into `/sandbox/cfg/keys/default/key.priv` or

```
root@3bot:/sandbox# echo -n 'PRIVATEKEYCONTENT' > /sandbox/cfg/keys/default/key.priv
root@3bot:/sandbox# cat /sandbox/cfg/keys/default/key.priv | wc -c
144
```

make sure the length is 144

##### Restore the secret

edit `/sandbox/cfg/jumpscale_config.toml` and set `SECRET` to the old secret.

when done do `jsx check`

##### Retrieve the words

execute that in kosmos `j.data.nacl.default.words`

NOTE: these words aren't compatible with the keys you have in 3bot connect

NOTE: You may have to delete `/sandbox/cfg/bcdb_config` and `pkill redis` if you got secret conflicts



### <a name='REMOTEHOSTIDENTIFICATIONHASCHANGED'></a>REMOTE HOST IDENTIFICATION HAS CHANGED

```
Could not execute:    scp -P 9010 root@localhost:/var/executor_data /tmp/jumpscale/scripts/35865.data

stderr:
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
    Someone could be eavesdropping on you right now (man-in-the-middle attack)!
    It is also possible that a host key has just been changed.
    The fingerprint for the ECDSA key sent by the remote host is
    SHA256:0NLL4zZubYiZ0hhSWAz/LB5VdCybIzfjZ/n0YlLLeBM.
    Please contact your system administrator.
    Add correct host key in /root/.ssh/known_hosts to get rid of this message.
    Offending ECDSA key in /root/.ssh/known_hosts:5
      remove with:
      ssh-keygen -f "/root/.ssh/known_hosts" -R "[localhost]:9010"
    ECDSA host key for [localhost]:9010 has changed and you have requested strict checking.
    Host key verification failed.
```
Just execute `ssh-keygen -f "/root/.ssh/known_hosts" -R "[localhost]:9010"`

### Chrome errors with certificate (OSX)

You can start chrome manually using
```
open -n -a /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome  --args --user-data-dir="/tmp/chrome_dev_test" --disable-web-security --ignore-certificate-errors'
```

### Permission denied during updating the on local storage jumpscale code
```
3sdk> simulator start

install & run a container with SDK & simulator
a connection to zerotier network will be made

param: code_update_force be careful, will remove your code changes


please provide secret (to locally encrypt your container):
please provide secret (to locally encrypt your container) (confirm):
 - SSH PORT ON: 9010
Using default tag: latest
latest: Pulling from threefoldtech/3bot2
Digest: sha256:f091e1d2acad6b41f47df00acd969a518ea6b67e43fa119a2ee15e5e6fdcb6b5
Status: Image is up to date for threefoldtech/3bot2:latest
docker.io/threefoldtech/3bot2:latest
 - Docker machine gets created:
82c9e54f9c5e181fad703a28a699854611046ea216f5763f9eb1eaf8049a4cab
 - Configure / Start SSH server
 - make sure jumpscale code is on local filesystem.
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/BillOfMaterial.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/NodesBatch.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/SimulatorBase.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/SimulatorConfig.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/TFGridSimulator.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/TFGridSimulatorFactory.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/__init__.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/BillOfMaterial.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/NodesBatch.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/SimulatorBase.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/SimulatorConfig.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/TFGridSimulator.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/TFGridSimulatorFactory.py': Permission denied
error: unable to unlink old 'JumpscaleLibsExtra/tools/threefold_simulation/notebooks/code/__init__.py': Permission denied
Could not checkout git@github.com:threefoldtech/jumpscaleX_libs_extra.git

    cd {REPO_DIR}
    git checkout -q . --force


3sdk>
```

Change ownership of `/sandbox` to you current user:
```bash
sudo chown -R $USER:$USER /sandbox
```
