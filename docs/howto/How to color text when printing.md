# How to color text when printing

![](images/color_text.png)

Colors understood:

- RED
- BLUE
- CYAN
- GREEN
- RESET
- BOLD
- REVERSE

RESET goes back to normal text, will be added to the text if not in there and colors used

example

```python
msg = "{BLUE} this is a test {BOLD}{RED} now red {RESET} go back to white"
print(j.core.tools.text_replace(msg,colors=True))
```