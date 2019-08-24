
# code & wiki parts

Is ability to mark blocks in code or wiki

marked as 

```
!!A!!
```

basically !!$MARKER!!

if you use 2 markers then basically marker will stop in next iteration

next examples will show how text with marker 'A' is taked out of the text

## Example 1

```
# title 1

## title 1.1 !!A!!

This is content

!!A!!
# title 2

Some other content

```

will result

```
## title 1.1

This is content

```

## Example 2

```
# title 1

!!A!!
## title 1.1 

This is content

!!A!!
# title 2

Some other content

```

will result

```
## title 1.1

This is content

```

## Example 3

```
# title 1

!!A!!
## title 1.1 

This is content !!A!!

# title 2

Some other content

```

will result

```
## title 1.1

This is content

```

## Example 4

```
# title 1

!!A!!


## title 1.1 

This is content 


!!A!!

# title 2

Some other content

```

will result

```
## title 1.1

This is content
```

there is always strip of '\n' at start & end

## Example 5 (python code)

```include('$NAME',part="CONSOLE")```


```python
class Console(j.baseclasses.object):  #!!CONSOLE!!
    """
    class which groups functionality to print to a console
    self.width=120
    self.indent=0 #current indentation of messages send to console
    self.reformat=False #if True will make sure message fits nicely on screen
    """
    #!!CONSOLE!!

    def xxx(self):
        pass
```

will result in  (for part CONSSOLE)

```python
class Console(j.baseclasses.object):
    """
    class which groups functionality to print to a console
    self.width=120
    self.indent=0 #current indentation of messages send to console
    self.reformat=False #if True will make sure message fits nicely on screen
    """
```

## Example 6 (python code with doc_only)

```include('$NAME',part="CONSOLE", doc_only=True)```


```python

class OTHER():
    pass

class Console(j.baseclasses.object):  #!!CONSOLE!!
    """
    class which groups functionality to print to a console
    self.width=120
    self.indent=0 #current indentation of messages send to console
    self.reformat=False #if True will make sure message fits nicely on screen
    """

    def X():
        """
        something
        """


    #!!CONSOLE!!

    def xxx(self):
        pass
```

will result in  (for part CONSSOLE)

```
class which groups functionality to print to a console
self.width=120
self.indent=0 #current indentation of messages send to console
self.reformat=False #if True will make sure message fits nicely on screen
something
```


## Example 6

```
# title 1

## title 1.1 !!A!!

This is content

# title 2

Some other content

```

will result

```
## title 1.1

This is content

# title 2

Some other content
```
