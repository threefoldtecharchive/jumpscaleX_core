from Jumpscale import j


class {{model.schema.key}}_model(j.baseclasses.threebot_crud_actor):
    def _init(self, **kwargs):
        self.bcdb = j.data.bcdb.instances.{{model.bcdb.name}}
        self.model = self.bcdb.model_get(url="{{model.schema.url}}")

    def new(self, **kwargs):
        """
        ```in
        {{fields_schema}}
        ```
        ```out
        res = (O) !{{model.schema.url}}
        ```
        """
        return super().new(**kwargs)

    def set(self, **kwargs):
        """
        ```in
        object_id = 0
        values = (dict)
        ```
        ```out
        res = (O) !{{model.schema.url}}
        ```
        """
        return super().set(**kwargs)

    def get_by_name(self, **kwargs):
        """
        ```in
        name = (S)
        ```
        ```out
        res = (O) !{{model.schema.url}}
        ```
        """
        return super().get_by_name(**kwargs)

    def get(self, **kwargs):
        """
        ```in
        object_id = 0
        ```
        ```out
        res = (O) !{{model.schema.url}}
        ```
        """
        return super().get(**kwargs)

    def find(self, **kwargs):
        """
        ```in
        query = (dict)
        ```
        ```out
        res = (LO) !{{model.schema.url}}
        ```
        """
        return super().find(**kwargs)

    def delete(self, **kwargs):
        """
        ```in
        object_id = 0
        ```
        """
        return super().delete(**kwargs)

    def destroy(self, **kwargs):
        return super().destroy(**kwargs)
