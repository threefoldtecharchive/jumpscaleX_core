from Jumpscale import j


class Package(j.baseclasses.threebot_package):
    def _model_get_fields_schema(self, model):
        lines = []

        for line in model.schema.text.splitlines():
            line = line.strip().lower()
            if line.startswith("@url"):
                continue
            lines.append(line)

        return "\n        ".join(lines)

    def prepare(self):
        models = list(j.data.bcdb.system.models.values())

        for model in models:
            model_url = model.schema.url
            if "bcdb" in model_url:
                continue

            shorturl = model_url.replace(".", "_")
            dest = self._dirpath + "/actors/" + shorturl + "_model.py"
            # for now generate all the time TODO: change later
            if True or not j.sal.fs.exists(dest):
                j.tools.jinja2.file_render(
                    self._dirpath + "/templates/ThreebotModelCrudActorTemplate.py",
                    dest=dest,
                    model=model,
                    fields_schema=self._model_get_fields_schema(model),
                    shorturl=shorturl,
                )
