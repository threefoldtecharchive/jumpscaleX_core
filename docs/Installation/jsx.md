
# JSX

## Main Commands

```bash
Usage: jsx [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  configure          initialize 3bot (JSX) environment
  container-clean    starts from an export, if not there will do the export...
  container-delete   delete the 3bot container :param name: :return:
  container-export   export the 3bot to image file, if not specified will
                     be...
  container-import   import container from image file, if not specified
                     will...
  container-install  create the 3bot container and install jumpcale inside...
  container-kosmos   open a kosmos shell in container :param name: name of...
  container-shell    open a shell to the container for 3bot :param name:...
  container-start    start the 3bot container :param name: :return:
  container-stop     stop the 3bot container :param name: :return:
  containers-reset   remove all docker containers :param name: :return:
  generate           generate the loader file, important to do when new...
  threebotbuilder    create the 3bot and 3botdev images
  install            install jumpscale in the local system (only supported...
  kosmos
```


## install

will install  kosmos in local system.

```bash
3BOTDEVEL:OSX:/: jsx install --help
Usage: jsx install [OPTIONS]

  install jumpscale in the local system (only supported for Ubuntu 18.04+
  and mac OSX, use container install method otherwise. if interactive is
  True then will ask questions, otherwise will go for the defaults or
  configured arguments

  if you want to configure other arguments use 'jsx configure ... '

Options:
  --configdir TEXT   default /sandbox/cfg if it exists otherwise ~/sandbox/cfg
  -w, --wiki         also install the wiki system
  --no-sshagent      do you want to use an ssh-agent
  -b, --branch TEXT  jumpscale branch. default 'master' or 'development' for
                     unstable release
  --pull             pull code from git, if not specified will only pull if
                     code directory does not exist yet
  -r, --reinstall    reinstall, basically means will try to re-do everything
                     without removing the data
  --help             Show this message and exit.
```

## install in a container

```bash
3BOTDEVEL:OSX:/: jsx container-install --help
Usage: jsx container-install [OPTIONS]

  create the 3bot container and install jumpcale inside if interactive is
  True then will ask questions, otherwise will go for the defaults or
  configured arguments

  if you want to configure other arguments use 'jsx configure ... '

Options:
  --configdir TEXT     default /sandbox/cfg if it exists otherwise
                       ~/sandbox/cfg
  -n, --name TEXT      name of container
  -s, --scratch        from scratch, means will start from empty ubuntu and
                       re-install everything
  -d, --delete         if set will delete the docker container if it already
                       exists
  -w, --wiki           also install the wiki system
  --portrange INTEGER  portrange, leave empty unless you know what you do.
  --image TEXT         select the container image to use to create the
                       container, leave empty unless you know what you do (-:
  -b, --branch TEXT    jumpscale branch. default 'master' or 'master' for
                       unstable release
  --pull               pull code from git, if not specified will only pull if
                       code directory does not exist yet
  -r, --reinstall      reinstall, basically means will try to re-do everything
                       without removing the data
  --no-interactive     default is interactive
  --help               Show this message and exit.
```

## threebotbuilder

`threebotbuilder` can be used to build and push all our 3bot images.

  We have four images:
- threefoldtech/base: pass `-b` to build it
- threefoldtech/3botdev: built by default
- threefoldtech/3bot: built by default
- threefoldtech/3bot-production: pass `-t` to build it

  to push all images, pass `-p` to the command

```bash
jsx threebotbuilder --help
Usage: jsx.py threebotbuilder [OPTIONS]

  create the 3bot and 3botdev images

Options:
  -p, --push        push to docker hub
  -b, --base        build base image as well
  -t, --production  build production image as well
  -c, --cont        don't delete continue a previously stopped run
  --help            Show this message and exit.

```

## other commands

use the built in help e.g. ```jsx install --help```
