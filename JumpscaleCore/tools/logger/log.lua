--[[

## dict keys:

- processid : a string id can be a pid or any other identification of the log
- cat   : optional category for log
- level : levels see https://docs.python.org/3/library/logging.html#levels
- linenr : nr in file where log comes from
- filepath : path where the log comes from
- context : where did the message come from e.g. def name
- message : content of the message
- data : additional data e.g. stacktrace, depending context can be different
- hash: optional, 16-32 bytes unique for this message normally e.g. md5 of eg. concatenation of important fields

### lOGGING LEVELS:

- CRITICAL 	50
- ERROR 	40
- WARNING 	30
- INFO 	    20
- DEBUG 	10
- NOTSET 	0

--]]


local data_in = ARGV[1]

local data = cjson.decode(data_in)

local processid = data["processid"]

if processid == nil or processid == '' then
    processid = "unknown"
end

local logkey = "logs:data:"..processid
local idkey = "logs:id:"..processid

local channelkey = "logs:channel:"..processid

local t = redis.call('TIME')[1]

local id = redis.call("INCR",idkey)

if id>1000 then
    redis.call("hdel", logkey, id-1000)
end

local v = {}
v[1] = id
v[2] = t --time
v[3] = tonumber(data["level"])
v[4] = data["message"]
v[5] = data["cat"]
v[6] = data["filepath"]
v[7] = data["linenr"]
v[8] = data["context"]
v[9] = data["data"]

local data = cmsgpack.pack(v)

redis.call("HSET",logkey,id,data)

redis.call("PUBLISH",channelkey,data_in)


return "OK "..id

