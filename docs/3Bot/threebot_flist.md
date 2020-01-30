# launch 3bot on the tfgrid using flist

### create your own threebot flist and upload it to hub
- ***Applicationid*** of itsyou.online
- ***SECRET*** of itsyou.online
- ***USER_NAME*** of hub.grid.tf

```python3
/tmp/jsx threebot-flist --app_id Applicationid --secret SECRET --username USER_NAME
```

###  launch the flist on a ZOS in TFGrid
- passing two env variables for coreX :
    ```buildoutcfg
    corex_user = COREX_USER_LOGIN
    corex_password = COREX_PASSWORD_LOGIN
    ```
- create port forward to 1500 ( default port) to see coreX page in web browser
