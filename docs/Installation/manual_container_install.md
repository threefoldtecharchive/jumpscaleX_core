## Manual local jumpscaleX_core

———-
Step 1:  Install the docker software.  There is a lot of documentation on how to do this for your operating system <<insert docker installation page link>>

Please check the installation by issuing the following commands:
```
Docker image ls
Docker ps
```

If this is successful you have a working docker environment! Now get yourself the latest (official) Ubuntu container:

```
Docker pull Ubuntu
```
This pulls in the office Ubuntu container from the docker hub and installs in onto your local system.  You can verify this by performing the following command:

```
Docker image ls
<<insert command output>>
```
We need to start the Ubuntu container. The rest of the installation will run inside the Ubuntu container. All of the modifications to the Ubuntu image will be stored inside the container.  This container will have the local installation of the jumpscale_coreX SDK.

Start the ubuntu container and login to a interactive (Unix) shell:
```
Docker run -ti ubuntu
```

The result of this command is a Unix prompt, representing the ```root``` user account of the ubuntu system. For here onwards we will configure the container to be a local installation of the jumpscalecoreX SDK.

First update the Ubuntu binaries to the latest version:
```
Apt update -y
```
Then add some additional software packages not part of the official container image:
```
apt install -y openssh-server locales curl git rsync unzip lsb python3 python3-pip
```
Then install a needed python package
```
pip3 install click
```
This is the complete update of the Ubuntu container to current patch levels. 

Now we start the installation the jumspcaleX_core SDK.  To do so we need an identity. We do this by configuring an RSA public and private key pair.
```
eval ssh-agent -s
```
This should return the process ID of the identity manger.  Then we create a public/private key pair
```
ssh-keygen
```
The binary will ask you where store the key pair - default answer is fine. It will then ask you to set a passphrase.  Just press enter twice or add an actual passphrase.

Next step is to get the public key added to the github account youown.  Look up your public key in on the chosen directory or of you opted for the default directory it should be this:
‘’’
Cd
Cd .ssh
More id_rsa.pub
```
Copy the text and add it to you github account. Please find instructions here how to do this. <<insert github documents how to add a public key>>

Once this is done - load the identity into your container root account:
```
ssh-add ~/.ssh/id_rsa
```
With the public key copied into the github account and the private key loaded in the container user account you now have access from the container to the github jumpscale repository.

Copy the install script to the local /tmp directory:
```
curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py?$RANDOM > /tmp/jsx;
```
Make the install script executable:
```
chmod +x /tmp/jsx;
```
Set the correct terminal output environment variables:
```
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
```
And then run the install script to do a local install
```
/tmp/jsx install
```

Et presto, you have have a local installation of the jumpscaleX_core environment in your container. Test it out by starting the kosmos shell:
```
Source /sandbox/env.sh
Kosmos
```

## In Dockerfile format

```
FROM ubuntu:latest
RUN apt update -y
RUN apt install -y openssh-server locales curl git rsync unzip lsb python3 python3-pip
RUN pip3 install click

RUN eval ssh-agent -s
RUN yes | ssh-keygen -N “”
RUN ssh-add ~/y
RUN echo "copy this public RSA key into your GitHub account, this is required by the rest of the install and will commence in 90 second"
RUN cat ~/y.pub
RUN sleep 90
RUN curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/master/install/jsx.py?$RANDOM > /tmp/jsx;
RUN chmod +x /tmp/jsx;
RUN export LC_ALL=C.UTF-8
RUN export LANG=C.UTF-8
RUN /tmp/jsx install
```
