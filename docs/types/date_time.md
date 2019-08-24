# date & time 

## duration

duration e.g. 1w, 1d, 1h, 1m, 1

- w = week
- d = day
- h = hour
- m = minute

translates to seconds when used


> there are many more types see ```j.data.types```

### <a name="date_supported_formats"></a> Date supported formats ( D ) 

- month/day  (will be current year if specified this way)
- year(4char)/month/day
- year(4char)/month/day
- year(2char)/month/day
- day/month/4char
- year(4char)/month/day

### <a name="date_time_supported_formats"></a> Date Time supported formats ( T )

- month/day 22:50
- month/day  (will be current year if specified this way)
- year(4char)/month/day
- year(4char)/month/day 10am:50
- year(2char)/month/day
- day/month/4char
- year(4char)/month/day 22:50
- +4h
- -4h

# Example

```python
SCHEMA = """
        @url = test.schema
        date_time = (t)
        date = (d)
        init_date_time = 01/01/2019 9pm:10 (t)
        init_date = 05/03/1994 (d)
        """
schema = j.data.schema.get(SCHEMA)
schema_obj = schema.new()
schema_obj.date_time = '2019/10/10 9:50'
schema_obj.date = '10/6/2019'
```