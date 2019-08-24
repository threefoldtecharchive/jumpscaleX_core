lapis = require "lapis"
lfs = require "lfs"

-- Load all applications
root = "applications"
all_apps = {}
for entity in lfs.dir(root) do
    if entity ~= "." and entity ~= ".." and string.sub(entity, -4) == ".lua" then
        app = string.sub(entity, 0, -5)
        all_apps[#all_apps + 1] = app


class extends lapis.Application
    @enable "etlua"
    for _, app in pairs all_apps
        @include "applications." .. app

    [index: "/"]: =>
        render: "home"
