# Deploy the 3bot

The 3bot that will be used to deploy the websites needs to be run with certain configurations initially. For each network (containing a webgateway)only 1 deploy website 3bot is required.
 


```
node1.container.create(flist='https://hub.grid.tf/three_bot_tft_1/3bot_autostart_development.flist',
nics=[{'type':'default','id':'None','hwaddr':'','name':'nat0'},{"name": "zerotier", "type": "zerotier", "id": "d3ecf5726d13091a"},{"name": "zerotier_ca", "type": "zerotier", "id": "c7c8172af1f387a6"}],
name='3bot_deploy',
hostname='3bot_deploy',
env='IP_GATEWAY':'10.243.52.81','PORT_GATEWAY':'6600','IP_NODE':'10.102.223.147','WEBGATEWAY_SERV_NAME':'wg'})
```
*flist* : The flist that contains the image of the 3bot that the container will run based on. In the case of deploy website 3bot: https://hub.grid.tf/three_bot_tft_1/3bot_autostart_development.flist

*nics* : network interfaces  
- In the above example the zerotier_ca (capacity) is needed to be able to create another container using the 3bot

*name* : name of container to be created

*hostname* : hostname of the container to be created

*env* : environment variables that will be passed to the 3bot container created
- *IP_GATEWAY*: IP of the web gateway to register the container with the website on
- *PORT_GATEWAY*: Port to be used to contact the webgateway robot
- *IP_NODE*: IP of the node to create the container on 
- *WEBGATEWAY_SERV_NAME*: name of the webgateway's service name (to register the domain name on that webgateway)



# Deploy a webiste using the 3bot
The deploy website 3bot can be used to deploy websites on either a caddy server or a ngnix server, based on some configurations. Using the interface the user provides the registered domain name, the github repository url containing the website data, as well as some data about the network where the website is to be living.

### Required data
1. **Domain name**: a domain name is registered using any domain name provider
2. **Github repository url**: the website data to be deployed should be in a github repo and the url is given in the following format: https://github.com/Incubaid/www_incubaid
3. **Branch**: the branch in the github repository to use
4. **JWT Token**: A JWT token retrieved using https://itsyou.online/ is required.To get a JWT token using the itsyouonline client click [here](https://github.com/threefoldtech/jumpscaleX/blob/development/docs/howto/get_jwt_with_itsoyouonline_client.md).
*note: Only JWT Tokens for users who are part of sys-admin iyo organization will be valid*
5. **Farm Zerotier ID** : Current support only for 'd3ecf5726d13091a'  
6. **Server option**:
    1. Caddy
        - The github repository should include in the root dir a Caddyfile that includes the required configurations such as the port that caddy will be running on
        - Port: port required in the 3bot flow should be the same port included in the Caddyfile
    2. Ngnix and Lapis
        - The github repository should have a certain structure with the following: 
            - views folder
            - static folder
            - filename.moon file (any filename with .moon extension that contains the logic of the website)
        - The previous directories should be known and given to the bot in order to do the required mappings to the files
        - note: the paths should be starting from inside the repo directly and start with '/'
7. Once the website is complete and registered on the webgateway, the bot will output 'The Website is ready'.
