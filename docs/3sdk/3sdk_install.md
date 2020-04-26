# Install 3sdk

* [Requirements](#Requirements)
* [3bot private key (3bot words)](#3botwords)
* [Install 3sdk command line](#Packagedinstallersdk)
* [Use 3sdk command line from source](#Using3sdkfromsource)


## <a name='Requirements'></a>Requirements

- Docker
- Chrome browser for OSX users

### <a name='3botwords'></a>Get your 3bot words

- From 3botconnect application go to settings, then show phrase to get your mnemonics
- Take a note of the 3bot name and your email
- When registering for the first time you can use these private words in your configurations
- These words are needed, they are your private key.

## <a name='Packagedinstallersdk'></a>Get 3sdk binaries

Binaries should be in the [release](https://github.com/threefoldtech/jumpscaleX_core/releases) page for osx and linux 

After downloading the 3sdk make them executable `chmod +x 3sdk`.

In terminal do

```
3sdk
```

- On OSX you probably will have to go to security settings & allow the os to start the 3sdk application.
- Now go to [3sdk_use](3sdk_use.md) to use the 3sdk to get yourself a 3sdk container on your system using docker.


## <a name='Using3sdkfromsource'></a>Using 3sdk from source (experts only)

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
 
Check [Troubleshooting](./3sdk_troubleshooting.md) for help.