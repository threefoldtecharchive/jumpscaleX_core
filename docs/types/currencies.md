# currencies

> values can be ```10%,0.1,100,1m,1k  m=million USD/EUR/CH/EGP/GBP``` are understood (+- all currencies in world)

- e.g.: 10%
- e.g.: 10EUR or 10 EUR (spaces are stripped)
- e.g.: 0.1mEUR or 0.1m EUR or 100k EUR or 100000 EUR

# Example

> kosmos  ' ``` j.clients.currencylayer.cur2usd_print()```'

> kosmos  ' ``` j.clients.currencylayer.cur2id```'

>  kosmos  ' ```j.clients.currencylayer.id2cur```'

```python
        SCHEMA = """
        @url = test.schema
        number = (N)
        currency = '100 usd' (N)
        """

        schema = j.data.schema.get(SCHEMA)
        schema_obj = schema.new()
        schema_obj.currency = "10 USD"
        currencies = j.clients.currencylayer.cur2usd

        for curr1 in currencies:
            value = 50 
            currency = '{} {}'.format(value, curr1)
            schema_obj.currency = currency
```