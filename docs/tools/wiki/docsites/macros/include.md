# Include macro

there is a lot of smartness around includes (is +- same as links), authors can use following

## how will doc generator find info

!!!include("wiki/links.md!LINK")

the name or path of part needs to be unique

if repo or docsite not mentioned then will look in current repo

## generic format

- how to use markers see [code_wiki_parts.md]

```
!!!include("$LINK")
```

- $LINK is the link info see previous section

## with markers

- how to use markers see [code_wiki_parts.md]

```
!!!include("wiki/links.md!LINK")
```

basically ! marks the PART name, in this case it will link to that section


## some python code

```
!!!include("console/Console.py!CONSOLE",doc_only=True)
```

## macro arguments  #TODO:*1 needs to be implemented in the doc generator macro include (the others can be removed)

### doc_only

- if True, means only documentation strings are being captured
- only relevant for .py files
- default = False

### remarks_skip

- if True, means skip all lines starting with '#' (after lstrip())
- only relevant for .py files
- default = False

### header_levels_modify = -2,-1,1,2...

- if 1 means every header level will be done +1 e.g. ## becomes ###
- if -1 means every header level will be done -1
    - e.g. ## becomes #
    - e.g. # stays # because is the top
- only relevant for markdown
- default = False

### ignore = []

- set of regex which will be ignored (is done per line)
- default = []

### codeblock_type

- will put result in code block of specified type e.g. ```python```
- default = None (means no codeblock)
