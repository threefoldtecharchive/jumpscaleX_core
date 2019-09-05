# Openresty Server
Webserver based on [nginx](https://www.nginx.com/) and [lapis](https://leafo.net/lapis/reference/getting_started.html)

## Components
### website:
website is equivalent to vhost in Nginx, it listens on a port and serves some locations

## Locations:
there are three types of locations
### 1- static location:
a location to serve static files  
**params**:  
path_url: the rout to this location  
path_location: directory of static files to be served  
index: the index file  

### 2- lapis location
path_url: the rout to this location
path_location: path to a directory contains `app.moon` file

### 3- proxy location
path_url: the rout to this location
ipaddr_dest: the destination ip address
port_dest: the destination port
schema: (http or https) for the destination server


## How to start 

![example archticture](examples/example_archticture.png)
