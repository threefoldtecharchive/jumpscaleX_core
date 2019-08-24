config = require "lapis.config"

config "development", ->
  port 80
  gedis_port 8888
  gedis_host '127.0.0.1'
  github_secret 'abdoabdo'

config "production", ->
  port 80
  num_workers 4
  code_cache "on"