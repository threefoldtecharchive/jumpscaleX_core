
# j.baseclasses.object_config_collection

Is the base class for a collection of config objects,
allowing you to create instances of the `_CHILDCLASS` on the fly.

## example

No params for init.

```python
class SSHClientFactory(j.baseclasses.object_config_collection_testtools):

    __jslocation__ = "j.clients.ssh"
    _CHILDCLASS = SSHClientBase

    def _init(self):
        #custom initialization
        self._something = {}

    def _childclass_selector(self,**kwargs):
        #EXAMPLE WHERE WE CHOOSE OTHER CHILD DEPENDING ENVIRONMENT
        if j.core.platformtype.myplatform.platform_is_osx:
            return SSHClientParamiko
        else:
            return SSHClient

    def test(self):
        '''
        js_shell 'j.clients.ssh.test()'
        '''

        s=j.clients.ssh.test1
        s.addr="a.b.c.d"
        s.port=1053
        s.sshkey_name="test"

        j.clients.ssh.test2.data_update(addr="a.b.c.e", port=1054, sshkey_name="test2", passwd="passwd")
        print (j.clients.ssh.test2)

        assert j.clients.ssh.test2.port == 1054


        #j.clients.ssh.test2.shell()  #NOT TO BE DONE IN TEST but can use to do ssh
```

![](images/configs_ssh_example.png)

- a,kds,w are instances to get to them do

```python
In [1]: j.clients.ssh.a
Out[1]:
sshclientparamiko
{
 "addr": "",
 "addr_priv": "",
 "allow_agent": true,
 "clienttype": "",
 "forward_agent": true,
 "login": "root",
 "name": "a",
 "passwd": "",
 "port": 22,
 "port_priv": 22,
 "proxy": "",
 "sshkey_name": "",
 "stdout": true,
 "timeout": 60
}
```

## methods

```python

class JSBaseConfigs(j.application.): TODO:

    def __init__(self):
        self._model = #IS THE JSMODEL, gets created automatically
        self._children = #ARE THE CHILDREN LINKED TO THIS CONFIGS OBJ, US ALWAYS OF 1 JSOBJECT TYPE

    def _bcdb_selector(self):
        """
        always uses the system BCDB, unless if this one implements something else
        """
        return j.application.bcdb_system

    def _childclass_selector(self),jsxobject:
        """
        allow custom implementation of which child class to use
        :return:
        """
        return self.__class__._CHILDCLASS

    def _trigger_add(self, method):
        """

        triggers are called with (jsconfigs, jsconfig, action)

        can register any method you want to respond on some change

        - jsconfigs: the obj coming from this class, the collection of jsconfigs
        - jsconfig: the jsconfig object
        - action: e.g. new, delete, get,stop, ...
        """

    def new(self, name, jsxobject=None, **kwargs):
        """
        :param name: for the CONFIG item (is a unique name for the service, client, ...)
        :param jsxobject: you can right away specify the jsxobject
        :param kwargs: the data elements which will be given to JSXObject underneith (given to constructor)
        :return: the service
        """
            if not jsxobject:
            jsxobject = self._model.new(data=kwargs)
            jsxobject.name = name
        jsxobject = self._childclass_selector(jsxobject)
        jsconfig = kl(parent=self, jsxobject=jsxobject)
        self._triggers_call(jsconfig, "new")
        self._children[name] = jsconfig
        return self._children[name]

    def get(self,name):
        """
        :param name: of the object
        """

    def reset(self):
        """
        will destroy all data in the DB, be carefull
        :return:
        """

    def find(self,**kwargs):
        """
        :param kwargs: e.g. color="red",...
                    e.g. id=...
        :return: list of the config objects
        """


    def count(self,**kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the config objects
        """


    def findData(self,**kwargs):
        """
        :param kwargs: e.g. color="red",...
        :return: list of the data objects (the data of the model)
        """

    def delete(self,name):
        """
        deletes the config with the name specified
        """

    def exists(self, **kwargs):
        """
        """
```

## Custom name

Should your `JSBaseConfigsClass` not be bound to a `__jslocation__` but be
one of the `__CHILDCLASSES` by overriding the `_name` class property of the `JSBaseConfigsClass` in question.

For example:

```python
from Jumpscale import j

class CountryClass(j.baseclasses.object_config_collection):
    """
    some text explaining what the class does
    """
    _CHILDCLASS = Province
    _name = 'country`
```
