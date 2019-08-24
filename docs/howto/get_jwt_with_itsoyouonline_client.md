# Get jwt from ItsYouOnline

## ItsYouOnline client instance

```
iyo = j.clients.itsyouonline.get(iyo_instance_name,
                                baseurl="https://itsyou.online/api",
                                application_id="application_id",
                                secret="secret")  

```
where:
- *iyo_instance_name* : name of itsyouonline instance to be used
- *application_id* : itsyouonline application id
- *secret* : itsyouonline secret associated with the application_id

    **note:** *application_id* and *secret* are obtained from settings -> API keys where there is already a valid account on itsyouonline

## Token generation
```
token = iyo.jwt_get(token_name).jwt
```
where:
- *token_name* : name of token to be generated