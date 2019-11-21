
## search replace trick

```
"/sandbox(.*)"
j.core.tools.text_replace("{DIR_BASE}$1")
```

the $1 will replace the (.*)


