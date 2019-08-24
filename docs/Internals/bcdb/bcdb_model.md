
# BCDB Model
## how to create your own model, not just starting from a schema

how to overrule the way how a model is loaded

use
```python
def _init_load(self,bcdb,schema,namespaceid,reset):
    #put your code here
    return bcdb,schema,namespaceid,reset
```

