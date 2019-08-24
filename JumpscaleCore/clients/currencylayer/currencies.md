
## currency layer

see https://currencylayer.com/

need to get a key there
when using the tool it will ask you to configure the client

do
```python
kosmos 'j.clients.currencylayer.cur2usd_print()'
```

should see something like
```
{'aed': 3.672804,
 'afn': 68.699997,
 'all': 107.099998,
 'amd': 480.299988,
 'ang': 1.780403,
 'aoa': 214.854996,
 'ars': 20.249001,
 'aud': 1.287704,
 'awg': 1.78,
 'azn': 1.699604,
 'bam': 1.589704,
 'bbd': 2,
 'bdt': 82.889999,
 'bgn': 1.5886040000000001,
 'bhd': 0.376504,
 'bif': 1750.97998,
 'bmd': 1,
 'bnd': 1.316904,
 'bob': 6.850399,
 'brl': 3.251704,
 'bsd': 1,
 'btc': 8.800000000000001e-05,
 'btn': 65.224998,
 'bwp': 9.582704,
 'byn': 1.9503979999999999,
 'byr': 19600,
 'bzd': 1.997804,
 'cad': 1.287804,
 'cdf': 1565.50392,
 'chf': 0.937604,
 'clf': 0.021980000000000003,
 'clp': 598.570007,
 ...
 ```

 ### can I use disconnected?


####  fake

```python
j.clients.currencylayer.fake = True
```


when this argument is set, it will allways used the local stored currencies,
it will not try to connect to internet, BE CAREFULL !!! date will not be up to date.

####  fallback

```python
j.clients.currencylayer.fallback = True
```

if you set this before using the class it will fallback when there is no network,
be careful because this uses currencies as stored in jumpscale so will not be up to date !!!




 ### each currency has a unique integer

 to see

```bash
kosmos 'j.clients.currencylayer.id2cur_print()'
kosmos 'j.clients.currencylayer.cur2id_print()'
```


```python
{1: 'aed',
 2: 'afn',
 3: 'all',
 4: 'amd',
 5: 'ang',
 6: 'aoa',
 7: 'ars',
 8: 'aud',
 9: 'awg',
 10: 'azn',
 11: 'bam',
 12: 'bbd',
 13: 'bdt',
 14: 'bgn',
 15: 'bhd',
 16: 'bif',
 17: 'bmd',
 18: 'bnd',
 19: 'bob',
 20: 'brl',
 21: 'bsd',
 22: 'btc',
 23: 'btn',
 24: 'bwp',
 25: 'byn',
 26: 'byr',
 27: 'bzd',
 28: 'cad',
 29: 'cdf',
 30: 'chf',
 31: 'clf',
 32: 'clp',
 33: 'cny',
 34: 'cop',
 35: 'crc',
 36: 'cuc',
 37: 'cup',
 38: 'cve',
 39: 'czk',
 40: 'djf',
 41: 'dkk',
 42: 'dop',
 43: 'dzd',
 44: 'egp',
 45: 'ern',
 46: 'etb',
 47: 'eur',
 48: 'fjd',
 49: 'fkp',
 50: 'gbp',
 51: 'gel',
 52: 'ggp',
 53: 'ghs',
 54: 'gip',
 55: 'gmd',
 56: 'gnf',
 57: 'gtq',
 58: 'gyd',
 59: 'hkd',
 60: 'hnl',
 61: 'hrk',
 62: 'htg',
 63: 'huf',
 64: 'idr',
 65: 'ils',
 66: 'imp',
 67: 'inr',
 68: 'iqd',
 69: 'irr',
 70: 'isk',
 71: 'jep',
 72: 'jmd',
 73: 'jod',
 74: 'jpy',
 75: 'kes',
 76: 'kgs',
 77: 'khr',
 78: 'kmf',
 79: 'kpw',
 80: 'krw',
 81: 'kwd',
 82: 'kyd',
 83: 'kzt',
 84: 'lak',
 85: 'lbp',
 86: 'lkr',
 87: 'lrd',
 88: 'lsl',
 89: 'ltl',
 90: 'lvl',
 91: 'lyd',
 92: 'mad',
 93: 'mdl',
 94: 'mga',
 95: 'mkd',
 96: 'mmk',
 97: 'mnt',
 98: 'mop',
 99: 'mro',
 100: 'mur',
 101: 'mvr',
 102: 'mwk',
 103: 'mxn',
 104: 'myr',
 105: 'mzn',
 106: 'nad',
 107: 'ngn',
 108: 'nio',
 109: 'nok',
 110: 'npr',
 111: 'nzd',
 112: 'omr',
 113: 'pab',
 114: 'pen',
 115: 'pgk',
 116: 'php',
 117: 'pkr',
 118: 'pln',
 119: 'pyg',
 120: 'qar',
 121: 'ron',
 122: 'rsd',
 123: 'rub',
 124: 'rwf',
 125: 'sar',
 126: 'sbd',
 127: 'scr',
 128: 'sdg',
 129: 'sek',
 130: 'sgd',
 131: 'shp',
 132: 'sll',
 133: 'sos',
 134: 'srd',
 135: 'std',
 136: 'svc',
 137: 'syp',
 138: 'szl',
 139: 'thb',
 140: 'tjs',
 141: 'tmt',
 142: 'tnd',
 143: 'top',
 144: 'try',
 145: 'ttd',
 146: 'twd',
 147: 'tzs',
 148: 'uah',
 149: 'ugx',
 150: 'usd',
 151: 'uyu',
 152: 'uzs',
 153: 'vef',
 154: 'vnd',
 155: 'vuv',
 156: 'wst',
 157: 'xaf',
 158: 'xag',
 159: 'xau',
 160: 'xcd',
 161: 'xdr',
 162: 'xof',
 163: 'xpf',
 164: 'yer',
 165: 'zar',
 166: 'zmk',
 167: 'zmw',
 168: 'zwl'}
```

