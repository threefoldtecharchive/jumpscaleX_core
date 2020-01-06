from Jumpscale import j


class SlideShow:
    def __init__(self):
        self.slides = []

    def slide_add(self, name, presentation_guid, footer, order):
        self.slides.append(Slide(name, presentation_guid, footer, order))

    def add_range(self, name, presentation_guid, range_start, range_end):
        for i in range(range_start, range_end + 1):
            self.slides.append(Slide(name, presentation_guid, order=i))

    def slides_get(self):
        return self.slides


class Slide:
    def __init__(self, name, presentation_guid, footer="", order=-1):
        self.name = name
        self.presentation_guid = presentation_guid
        self.footer = footer
        self.order = order


class Presentation:
    def __init__(self, name, presentation_guid, slides_count=0):
        self.name = name
        self.presentation_guid = presentation_guid
        self.slides_count = slides_count

    @property
    def slides_number(self):
        return self.slide_number

    @slides_number.setter
    def slides_number(self, value):
        self.slides_number = value


def is_valid_presentation_name(name, presentations):
    presentation = [item for item in presentations if name == item.name]
    if presentation is not None:
        return presentation.pop()
    else:
        raise Exception("error in parsing the slideshow, There is no presentation given with this name")


def get_slide_numbers(slide_numbers):
    return slide_numbers.split(",")


def get_slide_range(range, slides_count):
    ranges = range.split(":")
    start_range = ranges[0] if ranges[0] != "" else "1"
    end_range = ranges[1] if ranges[1] != "" else str(slides_count)
    return start_range, end_range


def get_slides_path():
    return j.sal.fs.joinPaths("sandbox", "var", "gdrive", "static", "slide")


def presentations_download(presentations):
    gdrive_cl = j.clients.gdrive.get(
        "slideshow_macro_client", credfile=j.core.tools.text_replace("{DIR_BASE}/var/cred.json")
    )
    slides_path = get_slides_path()
    j.sal.fs.createDir(slides_path)
    for presentation in presentations:
        slides_count = gdrive_cl.export_slides_with_ranges(presentation.presentation_guid, slides_path)
        presentation.slides_count = slides_count


def _content_parse(content):
    slideshow = SlideShow()
    parsed_toml = content
    presentations = list()
    for key, val in parsed_toml["presentation"][0].items():
        presentation = Presentation(key, val)
        presentations.append(presentation)
    # Download presentation and get presentation slide count
    presentations_download(presentations)
    for slide in parsed_toml["slideshow"]:
        presentation = None
        presentation_name = slide.get("presentation")
        slide_numbers = slide.get("slide")
        if presentation_name is not None:
            presentation = is_valid_presentation_name(presentation_name, presentations)
        else:
            raise Exception("error in parsing the slideshow, There is an error in the presentation name")
        if slide_numbers is not None:
            slides_numbers_list = list()
            if slide_numbers.find(",") != -1:
                slides_numbers_list = get_slide_numbers(slide_numbers)
            else:
                slides_numbers_list.append(slide_numbers)
        else:
            raise Exception("error in parsing the slideshow, There is an error in the slide name")
        for number in slides_numbers_list:
            if number.find(":") != -1:
                range_start, range_end = get_slide_range(number, presentation.slides_count)
                slideshow.add_range(
                    name="",
                    presentation_guid=presentation.presentation_guid,
                    range_start=int(range_start),
                    range_end=int(range_end),
                )
            else:
                slideshow.slide_add(
                    name="", presentation_guid=presentation.presentation_guid, footer="", order=int(number)
                )
    return slideshow


def slideshow_v2(doc, **kwargs):
    slides = _content_parse(kwargs)
    slides_path = get_slides_path()
    output = "```slideshow\n"
    for slide in slides.slides_get():
        filepath = f"{slides_path}/{slide.presentation_guid}/{str(slide.order)}.png"
        relative_path = j.sal.fs.joinPaths(doc.path_dir_rel, slide.presentation_guid, str(slide.order) + ".png")
        dest = j.sal.fs.joinPaths(doc.docsite.outpath, relative_path)
        j.sal.fs.copyFile(filepath, dest, createDirIfNeeded=True)
        image_tag = """
        <img src="$path{dest}" alt='{slide_name}'"/>
        """.format(
            slide_name=slide.order, dest=j.sal.fs.joinPaths(doc.docsite.name, relative_path)
        )
        output += """
            <section>
               <div class="slide-image">
                   {image}
                   <div style="font-size: 200%;">
                   {footer}
                   </div>
               </div>
            </section>""".format(
            image=image_tag, footer=slide.footer
        )
    output += "\n```"
    return output


# for future work we propose to use islice function to help in slicing
