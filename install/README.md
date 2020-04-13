# Installer



## Packaged installer (sdk)

To build, you need to have:
* `python3`
* `pip`
* `upx` is used to compress binary executable, can be installed with:
    * ubuntu: `apt-get install upx`
    * macos (using brew): `brew install upx`
* `pyinstaller` can be installed using `pip3 install pyinstaller --user`



### Build:

Run the packaging script:

```bash
cd install
./package.sh
```

If nothing gone wrong, you should find the final binary executable at `dist` directory.

Try running it with:

```bash
./dist/3sdk
```

## advanced (manual) 3sdk setup from source
This will require python3, git on the user system 

- `pip3 install jedi pudb ptpython==2.0.4`
- `cd /tmp && git clone https://github.com/threefoldtech/jumpscaleX_core/ && cd jumpscaleX_core && git checkout unstable && git pull`
- `sudo -s`
- `ln /tmp/jumpscaleX_core/install/3sdk.py /usr/bin/3sdk`




## using 3sdk

launch `3sdk`

![](images/3sdk2.png)

### Getting help

You can type `info` or `info()` and you will see a list of available commands that you can use.

![](images/3sdk3.png)


### to start a threebot container in one command


> `container threebot`


### Install a new container
> `container install name=notsomeuser3 identity=notsomeuser3 email=notsomeuser3@gmail.com server=True`

- server=True means to start 3bot server




### Running a new container

to start a new container `container start name:mycontainer`	



## Troubleshooting

### REMOTE HOST IDENTIFICATION HAS CHANGED

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
