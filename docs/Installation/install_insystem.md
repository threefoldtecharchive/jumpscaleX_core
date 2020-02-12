
# install in local system


```bash
python3 /tmp/jsx.py install
```

## OSX

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
source ~/sandbox/env.sh; kosmos
```

## Usage

* Kosmos in your terminal, type `kosmos`

* In Python

  ```bash
  python3 -c 'from Jumpscale import j;print(j.application.getMemoryUsage())'
  ```

  the default mem usage < 23 MB and lazy loading of the modules.
