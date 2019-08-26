from .EmailClient import EmailClient
from Jumpscale import j

JSConfigs = j.baseclasses.object_config_collection


class EmailFactory(JSConfigs):
    __jslocation__ = "j.clients.email"
    _CHILDCLASS = EmailClient

    def test(self):
        """
        js_shell 'j.clients.email.test()'
        """
        test_c = j.clients.email.test_c

        test_c.smtp_server = "localhost"
        test_c.smtp_port = 27
        test_c.login = "login"
        test_c.password = "password"
        test_c.Email_from = "test_c"

        test_c.save()

        assert j.clients.email.test_c.name == "test_c"
        assert j.clients.email.test_c.smtp_server == "localhost"
        assert j.clients.email.test_c.smtp_port == 27
        print("TEST OK")
