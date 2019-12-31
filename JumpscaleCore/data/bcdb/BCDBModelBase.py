from Jumpscale import j


class BCDBModelBase(j.baseclasses.object):
    def trigger_add(self, method):
        """
        see docs/baseclasses/data_mgmt_on_obj.md

        triggers are called with obj,action,propertyname as kwargs

        return obj or None

        :param method:
        :return:
        """
        if method not in self._triggers:
            self._triggers.append(method)

    def _triggers_call(self, obj, action=None, propertyname=None):
        """
        will go over all triggers and call them with arguments given
        see docs/baseclasses/data_mgmt_on_obj.md

        return obj, stop

        """
        model = self
        kosmosinstance = self._kosmosinstance
        stop = False
        for method in self._triggers:
            obj2 = method(model=model, obj=obj, kosmosinstance=kosmosinstance, action=action, propertyname=propertyname)
            if isinstance(obj2, list) or isinstance(obj2, tuple):
                obj2, stop = obj2
                if stop:
                    return obj, stop
            if isinstance(obj2, j.data.schema._JSXObjectClass):
                # only replace if right one returned, otherwise ignore
                obj = obj2
            else:
                if obj2 is not None:
                    raise j.exceptions.Base("obj return from action needs to be a JSXObject or None")
        return obj, stop
