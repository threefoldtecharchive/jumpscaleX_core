import json
from Jumpscale import j
from JumpscaleLibs.servers.mail.smtp import app
from JumpscaleLibs.servers.mail.bcdbmailbox import BCDBMailboxdir


class mail(j.baseclasses.threebot_actor):
    """
    """

    def _init(self, **kwargs):
        models = j.servers.imap.get_models()
        self.bcdb_mailbox = BCDBMailboxdir(models)

    def send(self, mail, schema_out=None, user_session=None):
        """
        ```in
        mail = (S)
        ```
        ```out
        success = (B)
        ```
        """
        if isinstance(mail, str):
            mail = json.loads(mail)
        app.store_mail(mail)
        out = schema_out.new()
        out.success = True
        return out

    def list(self, date_from, date_to, schema_out=None, user_session=None):
        """
        ```in
        date_from =  (D)
        date_to =  (D)
        ```
        ```out
        mail = (LO)
        ```
        """
        query = "WHERE date BETWEEN {} and {}".format(date_from, date_to)
        mails = self.bcdb_mailbox.get_messages(query)
        out = schema_out.new()
        our.mail = mails
        return out.mail

    def update_Folder_name(self, mail_id, folder_name, schema_out=None, user_session=None):
        """
        ```in
        mail_id =  (I)
        folder_name (S)
        ```
        ```out
        success = (B)
        ```
        """
        model = self.bcdb_mailbox.get_object(mail_id)
        self.bcdb_mailbox.rename_folder(model.folder, folder_name)
        out = schema_out.new()
        out.success = True
        return out

    def delete(self, mail_id, schema_out=None, user_session=None):
        """
        ```in
        mail_id =  (I)
        ```
        ```out
        success = (B)
        ```
        """

        self.bcdb_mailbox.remove(mail_id)
        out = schema_out.new()
        out.success = True
        return out

    def update_priority(self, mail_id, priority, schema_out=None, user_session=None):
        """
        ```in
        mail_id =  (I)
        priority = (B)
        ```
        ```out
        success = (B)
        ```
        """
        model = self.bcdb_mailbox.get_object(mail_id)
        model.priority = priority
        model.save()
        out = schema_out.new()
        out.success = True
        return out

    def receive(self, mail, schema_out=None, user_session=None):
        """
        ```in
        mail = (S)
        ```
        ```out
        success = (B)
        ```
        """
        if isinstance(mail, str):
            mail = json.loads(mail)
        app.store_mail(mail)
        out = schema_out.new()
        out.success = True
        return out

