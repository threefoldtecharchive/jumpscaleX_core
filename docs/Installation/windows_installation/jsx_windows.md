# JSX on windows

## Requirments

- Docker
 Download and install from [Here](https://hub.docker.com/editions/community/docker-ce-desktop-windows/)

## Components

- ### Dockerfile

This will build jsx image, configure it to be ready to use.

contents

```docker
FROM threefoldtech/3bot2

RUN eval `ssh-agent -s`; ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa -q -P ""; ssh-add ~/.ssh/id_rsa;
RUN curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/unstable/install/jsx.py > /tmp/jsx; chmod +x /tmp/jsx;
RUN /tmp/jsx configure -s --no-sshagent;

CMD . /sandbox/env.sh && kosmos "j.servers.threebot.start(with_shell=False)"

EXPOSE 80 443
```

This basically will use our `threefoldtech/3bot2` image to create jsx container(s), starts 3bot server within it, and exposes port 80 and 443

- ### Docker compose file

To spawn more than container we ill specify it in the docker container-compose file, we will define the ports for each container too

contents

```docker
version: '3'
services:
  jsx:
    build: .
    ports:
      - "4000:443"
      - "7000:80"
```

## How to install

- Install docker `gui based`

- Create a new folder and put the `Dockerfile` and `docker-compose.yml` file in it. you will find them next to this readme.

- then run `docker-compose up`

- wait untill creation is finished. you will see your container spawned at the end check using `docker ps`

- once it's done access it using `exec -it jsx_docker_jsx_1 bash` and init your threebot.

- Congratulations you now have your jsx loaded, access it in your browser using: http://localhost:7000/

**Note** if you made changes in your files make sure to run `docker-compose build` to see the changes
