# creating a chatflow

## chatbot actor
is located at `sandbox/code/github/threefoldtech/digitalmeX/packages/system/chat/actors/chatbot.py`


### defining a new chatflow

```python
from Jumpscale import j


def chat(bot):
    """
    to call http://localhost:5050/chat/session/whoami
    """

    res = {}
    name = bot.string_ask("What is your name?")
    age = bot.int_ask("What is your age? ")
    favorite_langs = bot.multi_choice(
        "Favorite language: ", ['python', 'perl', 'haskell', 'pascal'])
    worst_person = bot.single_choice(
        "Room with stalin, hitler and toby who would you shoot twice? ", ['stalin', 'hitler', 'toby'])

    R = """
    # You entered
    
    - name is {{name}}
    - age is {{age}}
    - favorite langs {{favorite_langs}}
    - worst person {{worst_person}}

    ### Click next 
    
    for the final step which will redirect you to threefold.me


    """
    R2 = j.tools.jinja2.template_render(text=j.core.text.strip(R), **locals())

    bot.md_show(R2)

    bot.redirect("https://threefold.me")
```

## loading chatflow

### configuring gedis server

```python
server = j.servers.gedis.configure(host='0.0.0.0', port=8888) 
```

### loading chatbot actor
```python
server.actor_add("/sandbox/code/github/threefoldtech/digitalmeX/packages/system/chat/actors/chatbot.py") 
```

### loading the chatflow directory
```python
server.chatbot.chatflows_load("/sandbox/code/github/threefoldtech/digitalmeX/packages/system/base/chatflows") 
server.start()  
```

## Interacting with the chatbot

The rules are
1- work_get: gets relevant question from the bot and must send a session id along with it
2- work_report: send the answer from the user to the chatbot
3- all the functions `*_ask` like `string_ask`, `int_ask` blocks the bot. until response is provided with work_report. 

### Example a chatflow with redis

``` 
127.0.0.1:8888>  default.chatbot.session_new '{"topic": "food_get"}'
{"sessionid": "783c3ba3-db65-4999-9d58-9d803e167de5"}
127.0.0.1:8888>  default.chatbot.session_new '{"topic": "whoami"}'
(error) ERR 'whoami'
127.0.0.1:8888>  default.chatbot.session_new '{"topic": "whoami"}'
{"sessionid": "9295ba31-9dfe-4fd4-8d57-290a35f6cdae"}
127.0.0.1:8888> default.chatbot.work_get '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae"}'
{"cat": "string_ask", "msg": "What is your name?", "kwargs": {}}
127.0.0.1:8888> default.chatbot.work_report '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae", "result":"ahmed"}'
(nil)
127.0.0.1:8888> default.chatbot.work_get '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae"}'
{"cat": "int_ask", "msg": "What is your age? ", "kwargs": {}}
127.0.0.1:8888> default.chatbot.work_report '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae", "result":500}'
(nil)
127.0.0.1:8888> default.chatbot.work_get '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae"}'
{"cat": "multi_choice", "msg": "Favorite language: ", "options": ["python", "perl", "haskell", "pascal"], "kwargs": {}}
127.0.0.1:8888> default.chatbot.work_report '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae", "result":["python", "haskell"]}'
(nil)
127.0.0.1:8888> default.chatbot.work_get '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae"}'
{"cat": "single_choice", "msg": "Room with stalin, hitler and toby who would you shoot twice? ", "options": ["stalin", "hitler", "toby"], "kwargs": {}}
127.0.0.1:8888> default.chatbot.work_report '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae", "result":"toby"}'
(nil)
127.0.0.1:8888> default.chatbot.work_get '{"sessionid" : "9295ba31-9dfe-4fd4-8d57-290a35f6cdae"}'
{"cat": "md_show", "msg": "# You entered\n\n- name is ahmed\n- age is 500\n- favorite langs ['python', 'haskell']\n- worst person toby\n\n### Click next \n\nfor the final step which will redirect you to threefold.me\n\n", "kwargs": {}}
```

## executing from the browser
TODO