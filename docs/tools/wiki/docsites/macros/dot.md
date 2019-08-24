# dot

This macro is used to convert [DOT language](https://en.wikipedia.org/wiki/DOT_(graph_description_language)) graphs to an image directly using `dot` command line (graphviz package should be installed).

### Examples

The following block will be replaced by a link to the graph image.

````
```
!!!dot
graph graphname {
    a -- b -- c;
    b -- d;
}
```
````

Will generate an image from the given graph and embed the link as following:

```
![image_name.png](image_name.png)
```

Final output:

![dot_output.png](images/dot_output.png
)
