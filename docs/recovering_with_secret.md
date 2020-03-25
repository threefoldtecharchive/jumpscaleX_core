# Recovering with a your existing key


To be able to recover you need to have that key JSX container configured with and `SECRET` as well

## for the key
 `cat /sandbox/cfg/keys/default/key.priv`

you can copy it to another file or just saved the content manually

## for the secret
`cat /sandbox/cfg/jumpscale_config.toml | grep SECRET`

 you can copy it to another file or just saved the content manually


To restore you copy the

## to restore the key
either copy the file back into `/sandbox/cfg/keys/default/key.priv` or

```
root@3bot:/sandbox# echo -n 'PRIVATEKEYCONTENT' > /sandbox/cfg/keys/default/key.priv
root@3bot:/sandbox# cat /sandbox/cfg/keys/default/key.priv | wc -c
144
```

make sure the length is 144

## to restore the secret

edit `/sandbox/cfg/jumpscale_config.toml` and set `SECRET` to the old secret.


when done do `jsx check`


if you got `odd length error` make sure your key doesn't have `\n` in the end.
