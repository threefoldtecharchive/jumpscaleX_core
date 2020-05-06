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