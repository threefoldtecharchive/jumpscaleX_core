
# what is a sal

- SAL = System Abstraction Layer
- ITS NOT a client, server or builder
- it talks to a locally installed component and does the configuration management

## remark

- a lot of code needs to be ported from Builder
- DO NOT use executor or prefab
- use only other sal's
- when using bash commands use the j.core.tools.text_replace function (to allow dir paths replacement)
- use caching (retry) if relevant

### DO NOT

- try not to use config management is best if a SAL's is 100% stateless
  - sometimes its needed to build up a structure in memory to create e.g. a config file
      - if you want to do this use the config manager classes but DON't save to the BCDB (ask Kristof if doubt)
