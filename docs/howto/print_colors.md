# how to use colors in your text?

When printing you can send color codes to your screen.

You just need to add our predefined color codes to your text and call:

``` j.core.tools.text_replace```


```python
MYCOLORS =   { "RED",
                "BLUE",
                "CYAN",
                "GREEN",
                "GRAY",
                "YELLOW",
                "RESET",
                "BOLD",
                "REVERSE"
                }
```

- don't forget to call reset  because this will revert to normal style

## example usage

```python

TEXT = """
U am playing with {RED} colors {RESET}.
Now back to black.
{GRAY}
- gray
- still
{RESET}
"""
#on next line ansi chars are inserted
text = j.core.tools.text_replace(TEXT)
print(text)

```
