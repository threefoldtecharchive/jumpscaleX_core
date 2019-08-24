
# Markers

Inside any document, markers can be added to mark sections or paragraphs.

They can be written in the format of `!!NAME!!`, start and end of any part of the document can be marked, if only start is specefied, it will assume the end is the next marker or it will be extended to the end of the file.

An example for a marker with name `A` that marks the start and end of a paragraph, and a marker `B` that only marks the start of another paragraph:

```
This is a document, full of content

    This is a paragaph !!A!!
such paragraph ends here !!A!!


    This is another paragraph, !!B!!
if it's at the end of the file, no need to specify the end marker
```
