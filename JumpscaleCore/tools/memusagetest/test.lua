local key = tostring(KEYS[1])
local data = tostring(KEYS[2])
local r
local data2
local lasttime=0


-- if redis.call("HEXISTS", "data:objects",key)==1 then
--     data2=redis.call("HGET", "data:objects",key)
-- --     local ecoraw=redis.call("HGET", "eco:objects",key)
-- --     local ecodb=cjson.decode(ecoraw)
-- --     eco["occurrences"]=ecodb["occurrences"]+1
-- --     lasttime = ecodb["lasttime"]
-- --     eco["lasttime"]=eco["epoch"]
-- --     eco["epoch"]=ecodb["epoch"]
-- --     eco["guid"]=ecodb["guid"]
-- --     eco["pushtime"]=ecodb["pushtime"] or 0
-- -- else
-- --     eco["occurrences"]=1
-- --     eco["pushtime"] = 0
-- --     eco["lasttime"]=eco["epoch"]

-- end

-- -- local delta = eco['occurrences'] or 0
-- -- if delta > 300 then
-- --    delta = 300
-- -- end
-- -- if eco["pushtime"] + delta < eco["lasttime"] then
-- --     eco["pushtime"] = eco["epoch"]
-- --     redis.call("RPUSH", "queues:eco",key)
-- -- else
-- --    redis.call("SADD", "eco:secos", key)
-- -- end

-- -- local ecoraw=cjson.encode(eco)
-- -- redis.call("HSET", "eco:objects",key,ecoraw)

-- -- -- keep redis clean
-- -- if redis.call("LLEN", "queues:eco") > 1000 then
-- --     local todelete = redis.call("LPOP", "queues:eco")
-- --     redis.call("HDEL","eco:objects",todelete)
-- -- end

-- -- if redis.call("HLEN", "eco:objects") > 1000 then
-- --     redis.call("DEL", "eco:objects")
-- -- end

--     r=redis.call("HSET", "data:objects:a:",key,data)

-- return ARGV[1]
