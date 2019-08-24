### Starting Open Publish:

after [configuring](./configure.md) open publish you can start it as following:

```bash
kosmos 'j.servers.threebot.start(background=True)'
```

#### Running OpenPublish tool will do the following:

##### 1 - pull/clone the following repos by default:
- [OpenPublish](https://github.com/threefoldtech/OpenPublish): which contains the base lapis files required for
publishing wikis and websites. It contains also the websocket and chatbot needed files.
[more details...](https://github.com/threefoldtech/OpenPublish)

- [Jumpscale Weblibs](https://github.com/threefoldtech/jumpscale_weblibs): which contains all required generic css/js
libs (i.e. bootstrap, gedis_client, jquery, docsify, ...etc)

Also it will link the Jumpscale Weblibs into the static directory of OpenPublish repo, so that you can just use it from
any website/wiki

##### 2 - Start the following servers in tmux:
- [Lapis](https://leafo.net/lapis/reference/getting_started.html) which will serve the web content using the
[OpenPublish](https://github.com/threefoldtech/OpenPublish) repo.
- [0-DB](https://github.com/threefoldtech/0-db). Note that you need to have zdb installed firstly, you can install it
by running `kosmos 'j.builders.db.zdb.install()'`
- [sonic](https://github.com/valeriansaliou/sonic). Note that you need to have sonic installed firstly, you can install it
by running `kosmos 'j.builders.apps.sonic.install()'`
##### 3 - Start the following servers in the same gevent loop (will be in tmux if used `background` option)
- [Gedis](https://github.com/threefoldtech/digitalmeX/tree/master/docs/Gedis): which loads the base actors
(chatbot, open_publish, sonic search, gdrive) and base chatflows
- [DNS Server](https://github.com/threefoldtech/digitalmeX/tree/master/DigitalMe/servers/dns): to be able to publish
wikis/websites using custom domains

Also the open publish actor which is by default loaded by gedis, auto pulls/updates deployed wikis/websites every
5 minutes by default.
