# chat package

Part of the core packages in threebot and defined [here](https://github.com/threefoldtech/jumpscaleX_threebot/blob/1c6764c8e1330c013588ec73912df25306336c5d/ThreeBotPackages/threebot/chat/README.md)

## Registaration

using the package manager
```
JSX> cl = j.servers.threebot.local_start_default()
JSX> cl.actors.package_manager.package_add("/sandbox/code/github/threefoldtech/jumpscaleX_threebot/ThreeBotPackages/threebot/chat")
JSX> cl.actors.package_manager.package_start("chat")
```

## Interacting with Chatflows

- go to `3BOT_URL/chat` to see list of available chats
- go to `3BOT_URL/chat/session/CHATFLOW_NAME` to go to specific chatflow

### Home page
![Chat Home](./images/chat/chathome.png)

Home page lists all of the registered chatflows


### Chatflow

We register a sample chatflow `food_get` in threebot

![Chat Flow1](./images/chat/chat1.png)
![Chat Flow2](./images/chat/chat2.png)
![Chat Flow3](./images/chat/chat3.png)
![Chat Flow4](./images/chat/chat4.png)
![Chat Flow5](./images/chat/chat5.png)


For more technical information on the chat package please check [Internals page](./internals.md)
