# from Jumpscale import j
from .ThreeBotActorBase import ThreeBotActorBase


class ThreeBotCRUDActorBase(ThreeBotActorBase):
    def new(self, **kwargs):
        user_session = kwargs.pop("user_session")
        # TODO: use user_session for authentication

        return self.model.set_dynamic(kwargs)

    def set(self, **kwargs):
        user_session = kwargs.pop("user_session")
        # TODO: use user_session for authentication

        id = kwargs.pop("object_id")
        values = kwargs.pop("values")
        obj = self.model.get(id)

        for key, val in values.items():
            setattr(obj, key, val)
        obj.save()
        return obj

    def get_by_name(self, **kwargs):
        return self.model.get_by_name(kwargs["name"])

    def get(self, **kwargs):
        return self.model.get(kwargs["object_id"])

    def find(self, **kwargs):
        return self.model.find(**kwargs["query"])

    def delete(self, **kwargs):
        user_session = kwargs.pop("user_session")
        # TODO: use user_session for authentication
        obj = self.model.get(kwargs["object_id"])
        obj.delete()

    def destroy(self, **kwargs):
        self.model.destroy()
