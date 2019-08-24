### Wiki Publish

Open publish enables user to publish new contents easily. To start publish your wiki content you will need the following:

1 - Create new repository for your contents on any SCM platforms (i.e. github) [more info about wikis](./wiki/README.md)

2 - The repo must have `docs` directory which will contains all the md files you need to publish

3 - It is better to have two branches for the repo, one for development and the other for production. The branches
must be called:

`master` => For production

`development` => For development

4 - [Start open publish](./servers_start.md)

5 - Using kosmos shell, connect to open publish actor using gedis client and publish the repo.
```python
gedis_client = j.clients.gedis.get(name="default", port=8888)
```
where you should change the following parameters if needed:

- name: The name of gedis client which could be any name
- port: The gedis port we used when [configured open publish](./configure.md)

```python
gedis_client.actors.open_publish.publish_wiki(name="foundation", 
                                              repo_url="https://github.com/threefoldfoundation/info_foundation/", 
                                              domain="foundation.grid.tf", 
                                              ip="172.17.0.2")
```
where you should change the following parameters if needed:

- name: The name of wiki you want to publish
- repo_url: The repo url which contains the md filed you need to publish
- domain: the domain you need to use to access the wiki
- ip: the ip of the server running open publish

After running the previous snippet, open publish tool will do the following:

- Clone the md repo twice, one with master branch and the other with the development branch with the suffix `-dev`.
- Generate markdown site docs from `docs` dir for both master and dev branches using [markdowndocs](https://github.com/threefoldtech/jumpscaleX/tree/development/docs/tools/wiki) tool.
- Create two virtual hosts for [OpenPublish](https://github.com/threefoldtech/OpenPublish) lapis repo inside `vhosts` directory. 
It uses the following convention:
```
wiki.$DOMAIN => Production (master branch)
wiki2.$DOMAIN => Development (devlopment branch)
``` 
where $DOMAIN is replaced using the domain used when published the wiki. 
- Configure lapis to serve the wikis without domains also using the following convention:
```
http://IP:8080/wiki/$NAME => Production (master branch)
http://IP:8080/wiki/$NAME_dev => Development (devlopment branch)
```
where $NAME is replaced by wiki name used when published it

- It will add the wiki as an entry in open publish tool configuration so that it will be auto pulled every 5 minutes.
- will register the domain into the dns server

### Removing wikis

1 - Make sure that open publish is running [Start open publish](./servers_start.md)

2 - Using kosmos shell, connect to open publish actor using gedis client and publish the repo.
```python
gedis_client = j.clients.gedis.get(name="default", port=8888)
```
where you should change the following parameters if needed:

- name: The name of gedis client which could be any name
- port: The gedis port we used when [configured open publish](./configure.md)

```python
gedis_client.actors.open_publish.remove_wiki(name="foundation")
```
