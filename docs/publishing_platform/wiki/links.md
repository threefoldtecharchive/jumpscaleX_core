# Links

Links can be written in a custom format that make it easy to reference other documents in current wiki or any external wiki or repository. The same format is still valid, so links can be full urls or a reference to a file in the same repository.

### Syntax

```
[description](link)
```

`link` can be in the following format

```
account:repository(branch):name_or_path!marker
```

This can be broken down into:
* `account`: github account or organization (optional)
* `repository`: github repository (optional)
* `branch`: branch (defaults to master) (optional)
* `name_or_path`: the name or full path of a document or file
* `marker`: marker name, see [markers](markers.md)) (optional)

If any optional part is not specefied, it will be replaced by current wiki or repository information (see the following examples).

### Examples

#### Regular links (full url)

```
[document][https://github.com/threefoldfoundation/info_tokens/tree/master/docs/document.md]
```

#### With account and repository

This link

```
[document][threefoldfoundation:info_tokens(master):docs/document.md]
```

Will be replaced by

```
[document][https://github.com/threefoldfoundation/info_tokens/tree/master/docs/document.md]
```

#### Without account
If the current document repository is located inside `https://github.com/threefoldfoundation` repo, the following link

```
[document][info_tokens(master):docs/document.md]
```

Will be replaced by

```
[document][https://github.com/threefoldfoundation/info_tokens/tree/master/docs/document.md]
```


#### A link to an issue in info_tokens

```
[Issue](info_tokens:#122)
```

Will be replaced by


```
[Issue][https://github.com/threefoldfoundation/info_tokens/issues/122]
```


