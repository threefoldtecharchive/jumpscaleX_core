
# install in local system

**PLEASE DO NOT USE MANUAL DOCKER COMMANDS, USE THE JSX TOOL AS MUCH AS POSSIBLE**

JumpscaleX is meant to be run as root.
Therefore is you try to install from code you need to be logged as root ```sudo python install.py``` will not work.


### Ubuntu

```bash
python3 /tmp/jsx.py install
```

### OSX

required steps:

- create /sandbox
- install brew
- create the dir with right permissions
- install using the install script



- make sure /sandbox has been created (sudo was probably required and then you need to give yourself permission)
- in 'share' in docker preferences you need to add /sandbox otherwise you will get

```bash
docker: Error response from daemon: Mounts denied:
The path /sandbox/code
is not shared from OS X and is not known to Docker.
You can configure shared paths from Docker -> Preferences... -> File Sharing.
See https://docs.docker.com/docker-for-mac/osxfs/#namespaces for more info.
```

```bash
#to install brew:
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# install requirements

brew install curl python3 git rsync

#create dir
sudo mkdir -p /sandbox; sudo chown -R "${USER}:staff" /sandbox

```

do the install

```bash
python3 /tmp/jsx.py install
```
## to use


```bash
source /sandbox/env.sh; kosmos
```

## Usage

* Kosmos in your terminal, type `kosmos`

* In Python

  ```bash
  python3 -c 'from Jumpscale import j;print(j.application.getMemoryUsage())'
  ```

  the default mem usage < 23 MB and lazy loading of the modules.
