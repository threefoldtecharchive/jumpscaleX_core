local lapis = require("lapis")
local lfs = require("lfs")
local util = require("lapis.util")
local os = require("os")
local WikiApp
do
  local _class_0
  local _parent_0 = lapis.Application
  local _base_0 = {
    ["/wiki/:doc_site(/*)"] = function(self)
      self.name = self.params.doc_site
      self.wiki_path = true
      local req = self.req.parsed_url
      local file = self.params.splat
      if self.req.headers['x-forwarded-proto'] == "https" then
        self.req.parsed_url.scheme = "https"
      end
      if file == nil then
        local root = "/sandbox/var/docsites/" .. self.name
        local dirs = {
          root
        }
        local all_pages = { }
        for _, dir in pairs(dirs) do
          for entity in lfs.dir(dir) do
            if entity ~= "." and entity ~= ".." then
              local full_path = dir .. "/" .. entity
              local mode = lfs.attributes(full_path, "mode")
              if mode == "file" and string.sub(entity, -3) == ".md" then
                local page
                page, _ = string.gsub(full_path, root .. "/", "")
                all_pages[#all_pages + 1] = page
              elseif mode == "directory" then
                dirs[#dirs + 1] = full_path
              end
            end
          end
        end
        self.all_pages = util.to_json(all_pages)
        local scheme = "ws"
        if self.req.parsed_url.scheme == "https" then
          scheme = "wss"
        end
        self.url = scheme .. "://" .. req.host
        if req.port then
          self.url = self.url .. ":" .. req.port
        end
        return {
          render = "wiki.index",
          layout = false
        }
      end
      if string.sub(file, -3) == ".md" then
        file = string.lower(file)
      end
      return {
        redirect_to = "/docsites/" .. self.name .. "/" .. file
      }
    end
  }
  _base_0.__index = _base_0
  setmetatable(_base_0, _parent_0.__base)
  _class_0 = setmetatable({
    __init = function(self, ...)
      return _class_0.__parent.__init(self, ...)
    end,
    __base = _base_0,
    __name = "WikiApp",
    __parent = _parent_0
  }, {
    __index = function(cls, name)
      local val = rawget(_base_0, name)
      if val == nil then
        local parent = rawget(cls, "__parent")
        if parent then
          return parent[name]
        end
      else
        return val
      end
    end,
    __call = function(cls, ...)
      local _self_0 = setmetatable({}, _base_0)
      cls.__init(_self_0, ...)
      return _self_0
    end
  })
  _base_0.__class = _class_0
  local self = _class_0
  self:enable("etlua")
  if _parent_0.__inherited then
    _parent_0.__inherited(_parent_0, _class_0)
  end
  WikiApp = _class_0
  return _class_0
end
