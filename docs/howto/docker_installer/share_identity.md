# Share identity between containers

It is possible to share identity of a previous 3bot container to a newly installed container.
After performing a threebot init the identity is stored in the shared host directory to be reused in other containers when specified.

Identity consists of:

- `priv.key`: Private key of the identity
- `conf.toml`: File containing extra information for the identity:
  - `SECRET`: required, secret used for the dientity
  - `ADMINS`: list of admins to be added to the container threebot

During `jsx container-install` if an identity is specified by using the option `--identity {identity_name}` it will start the container with that identity as follows:

- If identity exists on the shared directory(`{HOME}/sandbox/var/containers/shared/keys`) then it will use it
- If it doesn't it will create the identity but it will be required for the installation to be interactive to configure threebot init

If `--identity` option is not specified:

- If a single identity is present it will be used
- If multiple found will ask the user if interactive install otherwise it will fail
- Will create a new identity otherwise

At the end of the installation `j.tools.threebot.init_my_threebot` is called if the identity is specified whether by the user or choosen during installation.

In the case of no identity specified, it will be the responsibility of the user to init threebot after install.
