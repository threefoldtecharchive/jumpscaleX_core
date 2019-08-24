from Jumpscale import j
from .utils import get_msg_path

JSBASE = j.baseclasses.object


class attrdict(dict):
    def __getattr__(self, k):
        return self[k]

    def __dir__(self):
        atts = list(self.keys())
        atts.extend(dir(super()))

        return atts


def toattrdict(d):
    if isinstance(d, dict):
        d = attrdict(d)
        for k, v in d.items():
            if isinstance(v, dict):
                d[k] = toattrdict(v)

        return d
    return d


class Message(attrdict, JSBASE):

    """
Details about the message for which the event occurred.
    raw_msg 	the full content of the received message, including headers and content
    headers 	an array of the headers received for the message, such as `Dkim-Signature`, `Mime-version`, `Date`, `Message-Id`, etc.
    text 	the text version of the message
    html 	the HTML version of the message
    from_email 	the from email address for the message
    from_name 	the from name for the message
    to 	the recipients of the message, and their names
    email 	the email address where Mandrill received the message
    subject 	the subject line of the message
    tags 	the tags applied to the message
    sender 	the Mandrill sender of the message
    attachments 	an array of attachments for the message, with filenames as keys. If there are no attachments, key is omitted. Each attachment has the following keys:
            name 	the file name
            type 	the MIME type of the attachment
            content 	the attachment content
            base64 	boolean whether the attachment contents are Base64 encoded
    images 	an array of images for the message, with filenames as keys. If there are no images, key is omitted. Each image has the following keys:
            name 	the file name
            type 	the MIME type of the image
            content 	the image content
            base64 	boolean whether the image contents are Base64 encoded
    spam_report 	the results of processing the message with the default SpamAssassin rules. Contains the following keys:
            score 	the total spam score for the message
            matched_rules 	an array containing details about the rules that the message matched. Each rule entry contains the following keys:
            name 	the name of the rule
            description 	a short description of the rule
            score 	the score for this individual rule
            spf 	spf validation results, or null if an error occurred while checking SPF for the message. Contains the following keys:
            result 	the spf validation result. One of: pass, neutral, fail, softfail, temperror, permerror, none
            detail 	a human-readable description of the result
            dkim 	details about the message`s DKIM signature, if any
            signed 	boolean whether the message contained a DKIM signature (true or false)
            valid 	whether the message`s DKIM signature was valid. Always false if signed is false.
    """

    def __init__(self, key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        JSBASE.__init__()
        self._key = key
        self._cached = False

    def _cache(self):
        if self._key:
            self.update(util.get_json_msg(self._key))
            self._cache = True

    def _checkcached(self):
        if not self._cached:
            self._cache()

    @property
    def html(self):
        self._checkcached()
        return self.html

    @property
    def text(self):
        self._checkcached()
        return self.text

    @property
    def content(self):
        self._checkcached()
        return self.content


if __name__ == "__main__":
    m = {
        "raw_msg": "somethinggg",
        "headers": "somethinnnn1111",
        "text": "that the bodyyy",
        "from_email": "ahmed@there.com",
        "from_name": "ahmed",
        "to": "someone2",
        "email": "someone2 @there.com",
    }

    msg = Message(m)
    print(msg)
    print(msg.raw_msg)
