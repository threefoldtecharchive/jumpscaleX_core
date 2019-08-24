# numeric

- n, numeric 

> has support for currencies

- [for more details](currencies.md)

can be represented as string

- is a string representation of a number with potentially a currency symbol

e.g. ```10 USD```

## stored at backed as 6 or 10 bytes

# Example

```python
        scm = """
        @url = test.schema
        number = (N)
        currency = (N)
        init_numeric_1 = '10 usd' (N)
        init_numeric_2 = 10 (N)
        init_numeric_3 = 10.54 (N)
        """

        schema = j.data.schema.get(scm)
        schema_obj = schema.new()
        schema_obj.currency = "10 USD"
        currencies = j.clients.currencylayer.cur2usd

        for curr1 in currencies:
            value = 50 
            currency = '{} {}'.format(value, curr1)
            schema_obj.currency = currency
```