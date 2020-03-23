# 3bot deployer:
To allow the use of the chatflows for deployments through a deployer machine,  it needs to be setup with some configurations
### Prerequisites
   - Intsall [Jumpscale](../Installation/README.md)
   - Required Packages
    ```
    pip3 install base58
    ```
### configurations:
 -  Setup deployer env variable
```python
. /sandbox/env.sh kosmos -p
j.core.myenv.config["deployer"] = True
j.core.myenv.config_save()
```
   - Create s3 client on machine
```python
. /sandbox/env.sh kosmos -p
cl = j.clients.s3.get("deployer", accesskey_=AWS_ID, secretkey_=AWS_SECRET)
cl.save()
```

### Start 3bot:
```python
kosmos -p  "j.servers.threebot.start(background=True)"
```
