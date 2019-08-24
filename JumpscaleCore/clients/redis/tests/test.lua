local processid = KEYS[1]
local cat = KEYS[2]
local message = KEYS[3]

local logkey = "logs:data:"..processid
local idkey = "logs:id:"..processid
local channelkey = "logs:channel:"..processid
redis.replicate_commands()
local t = redis.call('TIME')[1]


local id = redis.call("INCR",idkey)

if id>1000 then
    redis.call("hdel", logkey, id-1000)
end

local v = {}
v[1] = id
v[2] = t --time
v[3] = tonumber(cat)
v[4] = message

local data = cmsgpack.pack(v)

local s = tostring(id).."|"..cat.."|"..message

redis.call("HSET",logkey,id,data)

redis.call("PUBLISH",channelkey,s)

--redis.breakpoint()

return "OK "..processid..cat..message

