# jsx configure

```bash
#jsx configure --help
Usage: jsx configure [OPTIONS]

  initialize 3bot (JSX) environment

Options:
  --debug               do you want to put kosmos in debug mode?
  -s, --no-interactive  default is interactive
  --privatekey TEXT     24 words, use '' around the private key if secret
                        specified and private_key not then will ask in -y mode
                        will autogenerate
  --secret TEXT         secret for the private key (to keep secret, also used
                        for admin secret on rbot), if not specified will be a random one
  --help                Show this message and exit.
  ```

these are the only configuration elements to be used to configure a 3bot/jsx environment.

## arguments

### secret & private key

The secret is used to encrypt your private key on the 3bot.
Without your private key you are lost and can never recuperate your private data.
The same secret is used as basis for your admin passwds as used in the personal server components like sonic, zdb, ...


## remarks from the past

- sshkey no longer needed, no longer used in our encryption schemas
