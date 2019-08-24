
## epoch

```python
j.data.time.epoch
#same as
j.data.time.getTimeEpoch()
```

## getTimeEpochBin

Get epoch timestamp (number of seconds passed since January 1, 1970) in binary format of 4 bytes

## getSecondsInHR

```python
j.data.time.getSecondsInHR()

In [7]: j.data.time.getSecondsInHR(36)
Out[7]: '36 seconds'

In [8]: j.data.time.getSecondsInHR(360)
Out[8]: '6.0 minutes'

In [9]: j.data.time.getSecondsInHR(365)
Out[9]: '6.1 minutes'

In [10]: j.data.time.getSecondsInHR(3650)
Out[10]: '1.0 hours'

In [11]: j.data.time.getSecondsInHR(3350)
Out[11]: '55.8 minutes'

In [12]: j.data.time.getSecondsInHR(3850)
Out[12]: '1.1 hours'
```