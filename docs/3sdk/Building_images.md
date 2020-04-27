## Building Jumpscale related images
```
docker login
```
### Building threefoldtech/phusion and threefoldtech/base images
```
3sdk --expert
3sdk> builder base
```
### building threefoldtech/3bot image
```
3sdk --expert
3sdk> builder sdk

```
### Push images
```
docker push threefoldtech/3bot2
```
