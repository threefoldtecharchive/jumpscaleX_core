import smtplib
from contextlib import contextmanager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from Jumpscale import j

JSBASE = j.baseclasses.object


class Sender(j.baseclasses.object):
    def __init__(self, username, password, host, port):
        JSBASE.__init__(self)
        self._host = host
        self._port = port
        self._username = username
        self._password = password

    @contextmanager
    def _connect(self):
        try:
            s = smtplib.SMTP(self._host, self._port)
            s.login(self._username, self._password)
            yield s
        finally:
            s.close()

    def send(self, to, from_, subject, content, content_type="plain", img=None):
        msg_root = MIMEMultipart("related")
        if isinstance(to, str):
            msg_root["To"] = to
        else:
            msg_root["To"] = ", ".join(to)

        msg_root["From"] = from_
        msg_root["Subject"] = subject
        if img:
            content += """
            <p>
            <img src="cid:image1">
            </p>
            """
        msg_html = MIMEText(content, content_type)
        if img:
            msg_img = MIMEImage(img, "png")
            msg_img.add_header("Content-ID", "<image1>")
            msg_img.add_header("Content-Disposition", "inline", filename="img")
        msg_root.attach(msg_html)
        if img:
            msg_root.attach(msg_img)
        with self._connect() as s:
            s.sendmail(from_, to, str(msg_root))
