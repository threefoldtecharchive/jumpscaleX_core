# templates

- we use the jinja templating engine to generate our code

performance is quite good:
we did some optimizations where we use hashing to make sure we don't lod templates if not needed

```python
~: kosmos 'j.tools.jinja2.test_performance()'

DURATION FOR:jinja_code
duration:0.13833117485046387
nritems:1000.0
performance:7229/sec

DURATION FOR:jinja_code2
duration:0.0999600887298584
nritems:1000.0
performance:10003/sec

DURATION FOR:jinja text
duration:0.06356000900268555
nritems:5000.0
performance:78665/sec
```

## python code render

```python
def code_python_render(self, obj_key="", path=None,text=None,dest=None,
                        objForHash=None,name=None, **args):
    """

    :param obj_key:  is name of function or class we need to evaluate when the code get's loaded
    :param objForHash: if not used then will use **args as basis for calculating if we need to render again,
            otherwise will use obj: objForHash
    :param path: path of the template (is path or text to be used)
    :param text: if not path used, text = is the text of the template (the content)
    :param dest: if not specified will be in j.dirs.VARDIR,"codegen",md5+".py" (md5 is md5 of template+msgpack of args)
                    or if name is specified will use the name  j.dirs.VARDIR,"codegen",name+".py
    :param args: arguments for the template (DIRS will be passed by default)
    :return:
    """
```

examples

```python
obj=j.tools.jinja2.code_python_render(obj_key="MyClass", path=path,reload=True, name="name:%s"%1)
```

## render any template

```python
def template_render(self,path=None,text=None,dest=None,reload=False, **args):
    """

    load the template, do not write back to the path
    render & return result as string

    :param path: to template (use path or text)
    :param text: text which is the template if path is not used
    :param dest: where to write the result, if not specified then will just return the rendered text
    :param reload, only relevant for path, when path exists and has been loaded before will not load again (only cached in memory)
    :param args: args which will be passed to the template engine
    :return:
    """
```

## information about jinja2

- http://jinja.pocoo.org/docs/2.10/

```

### Delimiters

{%....%} are for statements
{{....}} are expressions used to print to template output
{#....#} are for comments which are not included in the template output
#....## are used as line statements
```
### for loops

```
 {% for name in list_example %}
 <li>{{ name }}</li>
 {% endfor %}
```

## extends

/app/templates/base.html

```html
<! — “Parent Template” →
<!DOCTYPE html>
<html>
<head>
 {% block head %}
 <title>{% block title %}{% endblock %}</title>
 {% endblock %}
</head>
<body>
 {% block body %}{% endblock %}
</body>
</html>
```

/app/templates/index.html

```html
<! — “Child Template” →
{% extends “base.html” %}
{% block title %} Index {% endblock %}
{% block head %}
 {{ super() }}
{% endblock %}
{% block body %}
 <h1>Hello World</h1>
 <p>Welcome to my site.</p>
{% endblock %}
```

