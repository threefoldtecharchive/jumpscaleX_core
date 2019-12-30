from Jumpscale import j


class web_interface(j.baseclasses.object):
    __jslocation__ = "j.tools.packages.webinterface"

    def test(self, port=None, prefix="", scheme="http"):
        """
        kosmos `j.tools.packages.webinterface.test()'
        :return:
        """
        base_url = "0.0.0.0"
        if port:
            base_url = base_url + f":{port}"

        if prefix:
            base_url = base_url + f"/{prefix}"

        url = f"{scheme}://{base_url}"

        j.servers.threebot.local_start_default(background=True)
        gedis_client = j.clients.gedis.get(
            name="default", host="127.0.0.1", port=8901, package_name="zerobot.packagemanager"
        )

        gedis_client.actors.package_manager.package_add(
            j.core.tools.text_replace(
                "{DIR_BASE}/code/github/threefoldtech/jumpscaleX_core/JumpscaleCore/servers/gedis/pytests/test_package"
            )
        )
        gedis_client.reload()
        print("testing gedis http")
        assert (
            j.clients.http.post(
                f"{url}/zerobot/test_package/actors/actor/echo",
                data=b'{"args":{"_input":"hello world"}}',
                headers={"Content-Type": "application/json"},
            )
            .read()
            .decode()
            == "hello world"
        )
        print("gedis http OK")

        print("testing gedis websocker")
        from websocket import WebSocket
        import ssl

        ws = WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
        ws.connect(f"wss://{base_url}/gedis/websocket")
        assert ws.connected

        payload = """{
        "namespace": "default",
        "actor": "echo",
        "command": "actor.echo",
        "args": {"_input": "hello world"},
        "headers": {"response_type":"json"}
        }"""
        ws.send(payload)
        assert ws.recv() == "hello world"
        print("gedis websocket OK")

        print("tearDown")
        gedis_client.actors.package_manager.package_delete("zerobot.test_package")
        j.servers.threebot.default.stop()
