# Links

there is a lot of smartness around links, authors can use following

## how will doc generator find info

!!LINK!!
- all search is done lower case (so user can put any case, is ignored)
- when repo not specified then will always look in current repo (current repo is where doc is which uses the link)
- e.g ```schemas/readme.md``` will search over all paths in current repo and lower case match on ```schemas/readme.md```
    - e.g. ```see [schema documentation](docs/schemas/readme.md)``` just one more dir, to make sure only 1 match
- e.g ```readme.md``` will not work because probably there is more than 1 readme.md, in that case it will be error because more than 1 found
- e.g. ```jumpscaleX:schemas/readme.md``` will look for master branch on repo jumpscaleX, the repo will be looked for in same account as the one our doc is in (the doc which is having the link)
- e.g. ```jumpscaleX(development):schemas/readme.md``` will look for 'development' branch on repo jumpscaleX, the repo will be looked for in same account as the one our doc is in (the doc which is having the link)
- e.g. ```threefoldtech:jumpscaleX(development):schemas/readme.md``` will look for 'development' branch on repo jumpscaleX on github account threefoldtech
- e.g. ```#194``` will link to issue on github in same account/repo as doc
    - e.g. ```jumpscaleX:#194``` will link to issue on specified repo in current account
    - e.g. ```threefoldtech:jumpscaleX:#194``` will link to issue on specified account/repo
- e.g. ```https://github.com/threefoldtech/jumpscaleX/blob/development/docs/errors.md``` link to full blown url, will check http(s) untill found, will also checkout repo if not done yet
- e.g. ```[test link](data/schema/tests)``` would link to a directory because there is no extension like .py or .md, will have to check directory exists


TODO:*! some more examples and more detail, now very dense to understand

## link format

```
[optional](optional)
```

- ```see [schemas/readme.md]``` will create link ```[schemas]($real_destination_of_info)```
- ```see [](schemas/readme.md)``` will create link ```[schemas]($real_destination_of_info)```  is same as before
- ```see [schema info](schemas/readme.md)``` will create link ```[schema info]($real_destination_of_info)```

## how will the path be converted to the name of the link

- schemas/readme.md -> schemas
    - readme.md is removed
    - '/' is removed
- schemas/aaa.md -> aaa
- schemas/high_five.md -> 'high five'
    - _ becomes space
    - .md is removed



