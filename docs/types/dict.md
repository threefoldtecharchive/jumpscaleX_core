# dict
dictionary is an unordered collection of items. While other compound data types have only value as an element, a dictionary has a key: value pair.

Dictionaries are optimized to retrieve values when the key is known.

# Example
```python
      SCHEMA = """
        @url = test.schema.1
        info = (dict)
        init_dict = {"number": 468} (dict)
        """
schema = j.data.schema.get(SCHEMA)
schema_obj = schema.new()

schema_obj.info = {'number': 155}
```