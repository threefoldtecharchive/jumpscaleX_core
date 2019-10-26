from Jumpscale import j
import sys
import os
import gevent

THREEBOT_DOMAIN = "3bot.grid.tf"
PHONEBOOK_DOMAIN = f"phonebook.{THREEBOT_DOMAIN}"
NAME_MANAGER_DOMAIN = f"namemanager.{THREEBOT_DOMAIN}"
GRID_MANAGER_DOMAIN = f"gridmanager.{THREEBOT_DOMAIN}"


def restart_program():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = sys.executable
    os.execl(python, python, * sys.argv)


class registration(j.baseclasses.object):
    def _init(self, **kwargs):
        self.server = kwargs["gedis_server"]
        self.format = "json"

    def register(self, doublename, email, description, user_session=None):
        """
        ```in
        doublename = (S)
        email = (S)
        description = (S)
        ```
        """

        if not doublename:
            raise j.exceptions.Value("doublename cant not be empty")

        if email is None:
            raise j.exceptions.Value("email can not be empty")

        nacl = j.data.nacl.get("nacl")
        phonebook = j.clients.gedis.get(name="phonebook", host=PHONEBOOK_DOMAIN, port=8901)
        namemanager = j.clients.gedis.get(name="namemanager", host=NAME_MANAGER_DOMAIN, port=8901)
        j.clients.gedis.get(name="gridmanager", host=GRID_MANAGER_DOMAIN, port=8901)

        # Request a new id from the public Phonebook
        pubkey = nacl.verify_key_hex
        wallet_name, _ = doublename.split(".")
        phonebook.actors.phonebook.wallet_create(name=wallet_name)
        record = phonebook.actors.phonebook.name_register(name=doublename, pubkey=pubkey, wallet_name=wallet_name)
        sender_signature_hex = j.data.nacl.payload_sign(
            record.id, doublename, email, "", description, pubkey, nacl=nacl
        )
        phonebook.actors.phonebook.record_register(
            tid=record.id,
            name=doublename,
            email=email,
            description=description,
            pubkey=pubkey,
            sender_signature_hex=sender_signature_hex,
        )
        # Request ip address from the grid manager
        gridmanager_client = j.clients.gridnetwork.get("gridmanager")
        wireguard = gridmanager_client.network_connect("3botnetwork", doublename)
        # Request a record from the name manager
        privateip = wireguard.network_private.split("/")[0]
        signature = j.data.nacl.payload_sign(doublename, nacl=nacl)
        namemanager.actors.namemanager.domain_register(doublename, privateip, signature)

        content = "\n".join([f"nameserver {p.network_public}" for p in wireguard.peers_objects])
        j.sal.fs.writeFile("/etc/resolv.conf", content + "\n", append=False)

        print(f"Done, your url is: {doublename}.{THREEBOT_DOMAIN}")

    def reseed(self, newseed, user_session):
        exportpath = j.sal.fs.getTmpDirPath()
        j.data.bcdb.system.export(exportpath, False)
        j.data.nacl.configure(privkey_words=newseed)
        j.sal.process.execute(
            f"kosmos -p 'j.data.bcdb.system.destroy(); system = j.data.bcdb.get_system(); system.import(\"{exportpath}\")'"
        )
        # restart myself
        gevent.spawn_later(restart_program, 5)
