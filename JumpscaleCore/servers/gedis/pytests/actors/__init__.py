from Jumpscale import j

from .actor import SCHEMA_IN, SCHEMA_OUT

for schema in [SCHEMA_IN, SCHEMA_OUT]:
    j.data.schema.get_from_text(schema)
