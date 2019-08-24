
## basic performance testing

super easy to do

```python

j.tools.timer.start("something")
nr = 10000
for i in range(nr):
    #do something

j.tools.timer.stop(nr)

```

## performance & memory

```python
class TestClass(j.baseclasses.object):

    def test_basic_log(self,nr):
        for i in range(nr):
            self._log_log("a message",level=20)


        j.shell()


def main(self):
    """
    to run:

    kosmos 'j.tools.logger.test(name="memusage")'

    conclusion:
        base classes do not use that much mem
        30MB for 100.000 classes which become objects in mem

    """


    ddict = {}
    nr=100000
    j.tools.timer.start("basic test for %s logs"%nr,memory=True)
    for i in range(nr):
        ddict[str(i)]=TestClass()
    j.tools.timer.stop(nr)
```

result

```
DURATION FOR:basic test for 100000 logs
duration:0.2626361846923828
nritems:100000.0
performance:380754/sec
memory used: 31184.0
memory per item: 311.84
```
