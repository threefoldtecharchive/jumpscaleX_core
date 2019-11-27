import re


DOC_INFO_REGEX = r"([a-zA-Z]+)\/d\/([a-zA-Z0-9-_]+)"


def gpdf(doc, link, **kwargs):
    """generate pdf download link from google drive link to document or presentation

    :param doc: current document
    :type doc: Doc
    :param link: full url of document or presentation
    :type link: str
    :return: a download link to document/presentation as pdf
    :rtype: str
    """
    j = doc.docsite._j

    link = link.strip()
    match = re.search(DOC_INFO_REGEX, link)
    if match:
        doc_type, file_id = match.groups()
        if doc_type not in ("document", "spreadsheets", "presentation"):
            raise j.exceptions.Value(f"{doc_type} is not a supported document type ()")

        pdf_link = f"/wiki/gdrive/{doc_type}/{file_id}"
        # normal markdown links will be resolved by docsify, won't work
        return f"""```inline_html
            <a href="{pdf_link}">download as pdf</a>
        ```
        """
    raise j.exceptions.Value(f"cannot extract document type of id from an invalid link '{link}''")
