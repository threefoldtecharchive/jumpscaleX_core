
# how to use slideshow 
In this macro slideshow, a user can be easily create a slideshow from

- one or more presentations
- choose slides from these presentations ( using index or slide id)

# first create md file like this  :
```
!!!slideshow
presentation_1 = "https://docs.google.com/presentation/d/1DDVRHNIGiv7sPXP61Dt6hzwjhRRUdSDN8nz_vF_9XrQ/edit"

presentation_2 = "https://docs.google.com/presentation/d/1QRCmG9z6Oj5MhDhaI-l4Zo4OemiW3cgOrp_UBaxZVGc/edit?usp=sharing"

slide_1 = ["presntation_2[id.g54f44f9a7c_0_45]", "footer text"]
slide_2 =["presntation_1[id.p]", "footer"]
slide_3 =["presntation_2[id.p]", "footer"]
slide_4 =["presntation_1[id.g4d2e6bac17_0_0]", "footer"]
slide_5 = ["presntation_2[1]", "footer text"]
slide_6 =["presntation_1[2]", "footer"]
slide_7 =["presntation_2[2]", "footer"]
slide_8 =["presntation_1[1]", "footer"]

width = "5000"
height = "5000"

```
```
presentation_1 = url of presentaion (should be your own or public )
presentation_2 = url of presentaion (should be your own or public )
.
.
.
etc 
```
### we use slide that id **id.g54f44f9a7c_0_45** in **presentastion 2** and the footer is **footer text**  
```
slide_1 = ["presntation_2[id.g54f44f9a7c_0_45]", "footer text"]
```
### we use slide that number **1** in **presentastion 1** and the footer is **My slides** 
```
slide_2 = ["presntation_1[1]", "My slides"]
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