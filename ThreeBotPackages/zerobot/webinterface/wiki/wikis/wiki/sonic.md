# Sonic

## query(name, text)

This method will query a docsite, it accepts the following parameters:

- `name`: docsite name
- `text`: text to search for in all files

The result will be an object with `res` as a list of file paths relative to this docsite

## Examples

```
JSX> cl.actors.sonic.query('threefold.myjobs_ui', 'myjobs')
## actors.default.sonic.query.85a112766ed9b88b9cab802c1f483c64
 - res                 :
    - readme
```
