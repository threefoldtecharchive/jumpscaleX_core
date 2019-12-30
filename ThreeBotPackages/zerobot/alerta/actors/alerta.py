from Jumpscale import j


"""
JSX> anew = j.clients.gedis(...., port=8901)
JSX> anew.actors.alerta.list_alerts()
... a very long list
JSX> anew.actors.alerta.new_alert(
   severity=10,
   status="new",
   environment="ALL",
   service="JSX",
   resource="xmonader",
   event="event 1",
   value="n/a",
   messageType="error",
   text="rafir text")
## actors.default.alerta.new_alert.16c54214bfcd2a5b61f789be085a1d14
res                 : True
"""

STATES = ["closed", "new", "open"]
MESSAGE_TYPES = ["error", "info", "warn"]


class alerta(j.baseclasses.threebot_actor):
    def _init(self, **kwargs):
        self.alert_model = j.tools.alerthandler.model

    @j.baseclasses.actor_method
    def get_alert(self, alert_id, schema_out=None, user_session=None):
        """
        ```in
        alert_id = (I)
        ```

        """
        res = self.alert_model.find(id=alert_id)
        if res:
            return j.data.serializers.json.dumps(res[0]._ddict)
        return "{}"

    @j.baseclasses.actor_method
    def list_alerts(self, schema_out=None, user_session=None):
        alerts = j.data.serializers.json.dumps({"alerts": [alert._ddict for alert in self.alert_model.find()]})
        return alerts

    @j.baseclasses.actor_method
    def list_alerts_by_env(self, env_name="all", schema_out=None, user_session=None):
        """
        ```in
        env_name = (S)
        ```

        """
        if env_name.lower() == "all":
            alerts = self.alert_model.find()
        else:
            alerts = self.alert_model.find(environment=env_name)

        def map_enums(a):
            a["status"] = STATES[a["status"]]
            a["messageType"] = MESSAGE_TYPES[a["messageType"]]
            return a

        alerts = {"alerts": [map_enums(alert._ddict) for alert in alerts]}

        print("ALERTS: ", alerts)
        response = {"result": alerts, "error_code": "", "error_message": ""}
        return j.data.serializers.json.dumps(response)

    @j.baseclasses.actor_method
    def new_alert(
        self,
        severity=10,
        status="new",
        time=None,
        environment="all",
        service="JSX",
        resource="xmonader",
        event="event 1",
        value="n/a",
        messageType="error",
        text="error text",
        schema_out=None,
        user_session=None,
    ):
        """
        ```in
        severity=0 (I)
        status="closed,new,open" (E)
        environment = "" (S)
        service = "" (S)
        resource = "" (S)
        event = "" (S)
        value = "" (S)
        messageType = "error,info,warn" (E)
        text = "" (S)
        ```

        ```out
        res = (B)
        ```

        """
        alert = self.alert_model.new()
        alert.severity = severity
        alert.status = status
        alert.time = time or j.data.time.epoch
        alert.environment = environment
        alert.service = service
        alert.resource = resource
        alert.event = event
        alert.value = value
        alert.messageType = messageType
        alert.text = text

        alert.save()

        res = schema_out.new()
        res.res = True
        return res

    @j.baseclasses.actor_method
    def delete_all_alerts(self, schema_out=None, user_session=None):
        self.alert_model.destroy()

    @j.baseclasses.actor_method
    def delete_alert(self, alert_id, schema_out=None, user_session=None):
        """
        ```in
        alert_id = (I)
        ```
        """
        try:
            self.alert_model.delete(alert_id)
        except:
            pass
