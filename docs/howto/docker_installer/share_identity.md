# Share identity between containers

It is possible to share identity of a previous 3bot container to a newly installed container by following the next steps:

- Take a copy of the desired identity under `/sandbox/cfg/keys`
- Save the copy on host under `{HOME}/sandbox/var/containers/shared/keys`
- Get the secret of the old installation from `/sandbox/cfg/jumpsacle.config.toml`
- Write the secret to `{HOME}/sandbox/var/containers/shared/keys/{identity_name}/secret`
- When starting `container-install` add `--identity {name of identity}`

The container should now start with the old identity.
