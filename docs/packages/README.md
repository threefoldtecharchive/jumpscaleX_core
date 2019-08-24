# packages

## Intro

A package is functionality being added to digitalme

## types:

are subdirs of a package



- actors
    - is the logic inside a package
    - the code inside an actor should call as much as possible libraries in jumpscale (sals, clients, ...)
    - is also the implementation of our api for this package to the outside world, our interface basically
        - published  in webserver under:  $locationdm/$packagename/api/$restmethods (TO BE IMPLEMENTED)
    - also published in gedis under namespace $packagename
    - each file inside is an actor
- chatflows
    - interactive communication, implemented as chat bots
    - each file inside is a chat bot
- schemas
    - the models used in a package, is j.data.schema ...
    - each file inside is a schema
- docsites
    - markdown documentation sites, published underneith /wiki/$docsite_prefix/...
    - each subdir is a docsite
- docmacros
    - macro's as used in docsite(s)
    - each file inside is a docmacro (can be in subdirs)


## toml config items

### loader

is a specific config item which loads a git url in the local package.
When param dest not specified then it will scan for the directories as defined above and link them into the package

### web_prefixes

is list of prefixes on which flask will respond, needed to let the packages lazy load

## packages are stored in

- j.dirs.DATADIR + "dm_packages" + $PACKAGENAME

## schema used to store a package metadata

see

```
!!!include(
        name="Package.py",start_include=False,end_include=False
        giturl="https://raw.githubusercontent.com/threefoldtech/digital_me/{{JS9_BRANCH}}/DigitalMe/servers/digitalme",
        start="SCHEMA_PACKAGE",
        end="##ENDSCHEMA",
        )
```


## Example TOML

also explains what the meaning is of the metadata entries in the config format

```
!!!include(name="package.toml")
```
