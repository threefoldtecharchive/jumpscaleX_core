# get/add schema

## get

```python
j.data.schema.get_from_md5(md5):
    """
    :param md5: each schema has a unique md5 which is its identification string
    :return: Schema
    """

j.data.schema.get_from_url(url):
    """
    :param url: url is e.g. jumpscale.bcdb.user.1
    :return: will return the most recent schema, there can be more than 1 schema with same url (changed over time)
            most recent means the schema with the highest sid
    """

j.data.schema.get_from_text(schema_text):
    """
    will return the first schema specified if more than 1

    Returns:
        Schema
    """

```

### example


```python

SCHEMA="""
@url =  jumpscale.digitalme.package.1
name = "UNKNOWN" (S)           #any comment
abool = true (B)
"""
s=j.data.schema.get_from_text(SCHEMA)

#if the schema already exists then can do
s=j.data.schema.get_from_url(url="jumpscale.digitalme.package.1") #will die if not exists

#if the schema already exists then can do
md5 = s.md5  #get md5 from the schema above, the next should deliver same schema
s2=j.data.schema.get_from_md5(md5) #will die if not exists

assert ss==s2

```


## add

```python
j.data.schema.get_from_text(self, schema_text):
    """
    :param schema_text can be 1 or more schema's in the text
    :return a list with all schemas
    """



j.data.schema.add_from_path(self, path=None):
    """
    :param path, is path where there are .toml schema's which will be loaded
    :return a list with all schemas
    """
```

example

```python
j.data.schema.add_from_path(mpath)
s = j.data.schema.get_from_url("threefoldtoken.wallet")

```
