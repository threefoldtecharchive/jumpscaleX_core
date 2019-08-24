# Jumpscale Installation Prerequisites If You Install in System !

When not installing in system (docker) there are a lot less requirements.

Prior to installing Jumpscale you need the following elements:

* Mac OS X 10.7 (Lion) or newer or a linux OS (tested on ubuntu 18.04)
* Git installed with a github account
* an ssh key added to github
  * go [here](https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) to generate a ssh key
  * go [here](https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account) to add a ssh key to your github account
  * to list your public ssh keys `ssh-add -L`
* Curl
* Docker
  * [see docker-for-mac dmg install](https://docs.docker.com/v17.12/docker-for-mac/install/#download-docker-for-mac)
  * for servers/linux: installation [guide](https://docs.docker.com/v17.12/install/#server)
  * verify installation with `$docker --version`
* Python3
  * installation [guide](https://www.python.org/downloads/)
  * verify installation with `$python3 --version`
* pip3  
  * `$sudo apt install python3-pip`
* click python package  
  * `$pip3 install click`

<a name="osx"></a>
## OSX specifics
On OSX you probably want to install [homebrew](https://brew.sh), the package manager for macOS.

```bash
#to install brew:
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# install requirements
brew install curl python3 git rsync
```

## Next

Once the requirements here above are satisfied, you may start installing Jumpscale.

[See installation doc](/docs/Installation/README.md)

