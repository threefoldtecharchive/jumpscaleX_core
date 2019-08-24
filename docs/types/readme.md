# Jumpscale Types

Jumpscale X has a rich typeset if used properly can protect you with strongly typed features while python byitself is not typed.
The typesystem will automatically convert to the required type without you having to think about it.


- [currencies][currencies.md]
- [date_time][date_time.md]
- [dict][dict.md]
- [list][list.md]
- [numeric][numeric.md]


## Quick Overview

| Name | Symbol | Description | sample valid data |
| :----: | :------: | ----------- | --------- |
| String | S, str, string | can be any set of characters saved as string | "Hello !" |
| Integer| I, int, integer | can only be Integer numbers| 1, 2, 200, 1000 |
| Float  | F, float | just like the primitive float | 1.123, 1.0, 100.99 |
| Boolean| B, bool | can only be True of False |  y , 1 , yes , n , True, False |
| mobile |tel| can be set any mobile number| '+32 475.99.99.99' , '464-4564-464' , 468716420  |
| email |email| can be set any email | changeme@example.com |
| ipport |ipport| can be set only port  | 53  |
| ipaddress |ipaddr| can be set any IP Adress | '192.168.1.1' |
| ipaddressrange |iprange| can be set any IP Adress with range | '192.168.1.1/24' |
| Date   | D | date | 20/11/2018 . see [date supported formats](date_time.md)|
| Date Time   | T | date with time | 01/01/2019 9pm:10. see [date time supported formats](date_time.md)|
| Numeric| N, numeric | can store any numeric data including currencies [for details](numeric.md) | 1, 1.12, 10 USD, 90%, 10.5 EUR| 
| guid| guid | can store any guid   | 5b316587-7162-4bf1-99e6-fe53d9577cd0 | 
| dict| dict | can store any dict type [for details](dict.md)   | {"key":"value"} | 
| List  | l | stored as list directly   | [1,2,3] |
| yaml| yaml | can store any yaml    | "example:     test1" |
| multiline| multiline | string but with multiple lines   | "example \\n example2 \\n example3" |
| hash| h | hash is 2 value represented as 2 times 4 bytes   | 46:682 |
| bytes | bin | stored as bytes directly   | 'this is binary' |
| percent| p | to deal with percentages < 1 we multiply with 100 before storing   | 99 which would be 99% |
| url| u | Generic url type   | www.example.com  , 'test.example.com/home'|
