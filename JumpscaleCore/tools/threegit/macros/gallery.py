import requests
from Jumpscale import j

# html block example
"""
<div class="gallery">
	<a href="gallery/test_images/image1.jpg" class="big">
	<img src="gallery/test_images/thumbs/thumb1.jpg" alt="" title="">
	</a>
</div>
"""
# get images links from enduser
def gallery(doc, **kwargs):
    output = "```gallery\n"
    images_links = []

    for key in kwargs:
        if key.startswith("image"):
            images_links.append(kwargs[key])

    generated_html = render(images_links)
    output += generated_html
    output += "\n```"
    return output


# convert images & thumbs into html code
def render(images):
    blocks = ""
    for image in images:
        temp = """
			<a href="{}">
			<img src="{}" alt="{}" title="" width="300" height="300"/>
			</a>
		""".format(
            image, image, image
        )
        blocks += temp
    return blocks
