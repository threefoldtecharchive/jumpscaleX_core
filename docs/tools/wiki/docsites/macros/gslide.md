
# how to use gslide 
In this macro gslide, a user can be easily create a slideshow from

- one presentation


# first create md file like this  :
```
!!!gslide
presentation = "https://docs.google.com/presentation/d/1DDVRHNIGiv7sPXP61Dt6hzwjhRRUdSDN8nz_vF_9XrQ/edit"

width = "5000"
height = "5000"

```
```
presentation = url of presentaion (should be your own or public )

```


### the width and the height of slides is **5000px X 5000px**
```
width = "5000"
height = "5000"
```

## Get credentials

Using [Google console](https://console.developers.google.com/flows/enableapi?apiid=slides.googleapis.com)

### Service account 
- Create project 
- Create credentials (type service account)
You need to enable and download credentials files using  or go to [Python Quickstart](https://developers.google.com/slides/quickstart/python) and choose enable slides API then download configurations.
- Download credentials (as json and save it anywhere on your filesystem)

## should rename this file to **cred.json** and add it to /sandbox/var 

## load your macro :
 using kosmos 
 ```
url = "url in github that have your md file" 
tf_slides = j.tools.markdowndocs.load(url, name="slides") 
tf_slides.write()  

j.tools.markdowndocs.webserver()
 ```

open it at **localhost:8080/wiki/slides**