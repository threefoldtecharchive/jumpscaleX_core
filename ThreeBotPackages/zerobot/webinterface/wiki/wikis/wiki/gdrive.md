# Gdrive
This actor provides a way to get a download link for gdrive documents.

Note that this actors need a service account to be set, see [service account setup](https://github.com/threefoldtech/jumpscaleX_threebot/blob/development/docs/wikis/tech/README.md#setting-up-gdrive-and-service-account) documention for more.


## file_get(doctype, guid1, guid1)

Will return an object with `res` that contains a relative link to the file.

Accepts the following parameters:

- `doctype`: document type, one of document spreadsheets, presentation and slide.
- `guid1`: the GUID of the document
- `guid2`: the GUID of sub-items like a slide in a presentation


## Examples

```
JSX> cl = j.clients.gedis.get(name="threebot", port=8901, namespace="default")
system__system
system__system
JSX> cl.actors.gdrive.file_get('document', '1z_B9_sPob88AwFWJbYAhu58T58m8YRj-IpcnrcGye5w')
default__gdrive
## actors.default.gdrive.file_get.e0b4c80da14d4999d989aaa13e532074
 - res                 : /gdrive_static/document/1z_B9_sPob88AwFWJbYAhu58T58m8YRj-IpcnrcGye5w.pdf
 - error_message       :
 - error_code          : 0
```
