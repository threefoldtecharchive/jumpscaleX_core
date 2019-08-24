
```\
#make sure we are logged in into docker
docker login
cd /tmp
#export filesystem of created docker
#make sure we loose the layers by exporting
docker export 3bot -o /tmp/3bot.tar
#now import the tar into 1 layer will be smaller
docker import /tmp/3bot.tar despiegk/3bot
docker push despiegk/3bot
```