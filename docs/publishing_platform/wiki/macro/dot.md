# Dot

This macro can be used to generate a graph image directly from [DOT language](https://en.wikipedia.org/wiki/DOT_(graph_description_language)).

### Syntax:
Inside a code block as following

````
```
!!!dot
graph ... {
}
```
````

### Examples

The following code block
````
```
!!!dot
graph graphname {
    a -- b -- c;
    b -- d;
}
```
````

will be replaced by a link to this graph image directly

![dot_output.png](images/dot_output.png)
