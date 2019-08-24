
# install

**PLEASE DO NOT USE MANUAL DOCKER COMMANDS, USE THE JSX TOOL AS MUCH AS POSSIBLE**

- make sure docker installed
- only tested on Ubuntu & OSX

```bash
python3 /tmp/jsx.py container-install
```
will install in docker, delete if exists and starting from already created docker image (is faster)

The container image has a volume to the code on your local machine inside /sandbox/code. If you edit the code you can then test it inside the container. So no need to edit anthing inside the container, can use your std IDE to edit code.

## requirements on OSX

```bash
#to install brew:
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# install requirements

brew install curl python3 git rsync
```

## to use

```bash
#to get container kosmos shell (JSX)
python3 /tmp/jsx.py container-kosmos
#to get shell of the ubuntu base os underneath in the container
python3 /tmp/jsx.py container-shell
``` 
