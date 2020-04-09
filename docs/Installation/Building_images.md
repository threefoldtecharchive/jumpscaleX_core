## Building Jumpscale related images
```
curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/development/install/jsx.py?$RANDOM > /tmp/jsx;
chmod +x /tmp/jsx
docker login
```
### Building threefoldtech/phusion and threefoldtech/base images
```
/tmp/jsx basebuilder --push # --push will push the image after building
```
### building threefoldtech/3bot image
```
/tmp/jsx threebotbuilder --push # to push the threebotbuilder
```
or if you want to build base and threebotbuilder as well in one step
```
/tmp/jsx threebotbuilder --push --base # to push the threebotbuilder
```

