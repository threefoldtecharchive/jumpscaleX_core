
* [Requirements](#Requirements)
* [Using 3sdk](#Using3sdk)
	* [Getting help](#Gettinghelp)
	* [Basic Features](#BasicFeatures)
		* [Start Threebot Container (one command)](#StartThreebotContaineronecommand)
		* [Install New Container](#InstallNewContainer)
		* [Running New Container](#RunningNewContainer)
		* [Listing Containers](#ListingContainers)
		* [Accessing Container Shell](#AccessingContainerShell)
		* [Getting Container Kosmos](#GettingContainerKosmos)
	* [Advanced features](#Advancedfeatures)
* [Packaged installer (sdk)](#Packagedinstallersdk)
* [Using 3sdk from source](#Using3sdkfromsource)

## <a name='Requirements'></a>Requirements
- Docker
- Chrome browser for OSX users


## Know your 3bot words

- From 3botconnect application go to settings, then show phrase to get your mnemonics
- Take a note of the 3bot name and your email
- When registering for the first time you can use these private words in your configurations


## <a name='Using3sdk'></a>Using 3sdk

Binaries should be in the [release](https://github.com/threefoldtech/jumpscaleX_core/releases) page for osx and linux 

After downloading the 3sdk make them executable `chmod +x 3sdk`.

launch `3sdk`

![](images/3sdk2.png)

### <a name='Gettinghelp'></a>Getting help

You can type `info` and you will see a list of available commands that you can use.

![](images/3sdk3.png)

### <a name='BasicFeatures'></a>Basic Features

### Using the 3botconnect app words (mnemonics)

- You have to use same username & same email

#### <a name='StartThreebotContaineronecommand'></a>Start Threebot Container (one command)


> `container threebot`

```
3sdk
Welcome to sdk shell, for help, type info, to exit type exit
3sdk> container threebot                                                                                                                
Which network would you like to register to? 
make your choice (mainnet,testnet,devnet,none): testnet
what is your threebot name (identity)?
example.3bot
Configured email for this identity is me@example.com
Copy the phrase from your 3bot Connect app here.
your words from your 3bot application need to be entered here
specify secret to encrypt your data:
specify secret to encrypt your data (confirm):
```


#### <a name='InstallNewContainer'></a>Install New Container
> `container install name=notsomeuser3 identity=notsomeuser3 email=notsomeuser3@gmail.com server=True`

- server=True means to start 3bot server


#### <a name='RunningNewContainer'></a>Running New Container

to start a new container `container start name=mycontainer`	

#### <a name='ListingContainers'></a>Listing Containers

```
3sdk> container list  
 
list the containers 

  
 - notsomeuser3 : localhost       : threefoldtech/3bot2       (sshport:9000)
 - notsomeuser4 : localhost       : threefoldtech/3bot2       (sshport:9010)
 - 3bot       : localhost       : threefoldtech/3bot2       (sshport:9020)
3sdk>  
```
also using the sshport information you can do `ssh root@localhost -p $SSH_PORT` to manually ssh into the 

#### <a name='AccessingContainerShell'></a>Accessing Container Shell

Either use the sshport info from `container list` command and `ssh root@localhost -p $SSH_PORT` or just execute `container shell` and optionally give it the name of your container

#### <a name='GettingContainerKosmos'></a>Getting Container Kosmos

Execute `container kosmos` to get into kosmos shell



### <a name='Advancedfeatures'></a>Advanced features

##### installing 3bot on the host

just `install` in 3sdk

##### Controlling code branches

use `core branch` command



## <a name='Packagedinstallersdk'></a>Packaged installer (sdk)

To build the SDK yourself, you need to have:
* `python3`: 
    * ubuntu: `apt-get install python3`
    * macos: `brew install python3`
* `pip`: 
    * ubuntu: `apt-get install python3-pip`
    * macos (if not already part of the python3 installation, depends on the version): `brew install python3-pip`
* `upx` is used to compress binary executable, can be installed with:
    * ubuntu: `apt-get install upx`
    * macos (using brew): `brew install upx`
* `patchelf` (only needed on linux): 
    * ubuntu: `apt install patchelf`
* `pyinstaller` can be installed using `pip3 install pyinstaller --user`



### <a name='Build:'></a>Build:

Run the packaging script:

```bash
cd install
./package.sh
```

If nothing goes wrong, you should find the final binary executable at `dist` directory.

Try running it with:

```bash
./dist/3sdk
```

## <a name='Using3sdkfromsource'></a>Using 3sdk from source
This will require python3, pip3 and git on the user system 

```
mkdir -p ~/sandbox/code/github/threefoldtech/
cd ~/sandbox/code/github/threefoldtech/
git clone -b development https://github.com/threefoldtech/jumpscaleX_core/
cd jumpscaleX_core/install
# on Linux
pip3 install --user -e .
# On Mac
pip3 install -e .
```
 
Check [Troubleshooting](./troubleshooting.md) for help.