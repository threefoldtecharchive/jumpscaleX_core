# launch 3bot on the tfgrid using flist

### create your own threebot flist and upload it to hub
- ***Applicationid*** of itsyou.online
- ***SECRET*** of itsyou.online
- ***USER_NAME*** of hub.grid.tf

```python3
/tmp/jsx threebot-flist --app_id Applicationid --secret SECRET --username USER_NAME
```

###  launch the flist on a ZOS V2 in TFGrid:

- first should build ```tfuser``` tool from
https://github.com/threefoldtech/zos/tree/master/docs/tfuser

- **create your user id**:


   ``` tfuser id ```
- **Then create your network and your wireguard configure** :
    - get Node_ID from https://cockpit.devnet.grid.tf/
```

    tfuser generate --schema network.json network create --name NETWORK_NAME --cidr 172.20.0.0/16

    tfuser generate --schema network.json network add-node --node NODE_ID --subnet 172.20.1.0/24

    tfuser generate --schema network.json network add-access --node NODE_ID --subnet 10.1.0.0/24 --ip4
```

- **Then copy the config of wireguard and up your wireguard using your config**


    ``` sudo wg-quick up /etc/wireguard/demo.conf ```

- **provision your network to your node**:

```
    tfuser provision --schema network.json --duration 60 --seed user.seed --node NODE_ID
```
- **create extra mount for directory that contain bcdb and logs files**:


```
    tfuser generate storage volume --size 10 --type SSD > amount.json

    tfuser provision --schema amount.json --duration 8h --seed user.seed --node NODE_ID
```

- **create container of threebot**:
    - passing two env variables for coreX :
        ```buildoutcfg
        corex_user = COREX_USER_LOGIN
        corex_password = COREX_PASSWORD_LOGIN
        ```

```
    tfuser generate --schema ubuntu.json container --flist  https://hub.grid.tf/bola_nasr_1/threefoldtech-3bot-corex.flist --ip 172.20.1.20 --network NETWORK_NAME  --entrypoint "/usr/bin/zinit init -d"  --envs corex_user=COREX_USER_LOGIN --envs  corex_password=COREX_PASSWORD_LOGIN  --mounts STORAGEID:/sandbox/var > ubuntu.json
    tfuser provision --schema ubuntu.json --duration 5h --seed user.seed --node NODE_ID
```
- coreX page in web browser  ```172.20.1.20:1500```
