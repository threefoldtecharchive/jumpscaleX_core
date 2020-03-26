FROM threefoldtech/3bot2

RUN eval `ssh-agent -s`; ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa -q -P ""; ssh-add ~/.ssh/id_rsa;
RUN curl https://raw.githubusercontent.com/threefoldtech/jumpscaleX_core/unstable/install/jsx.py > /tmp/jsx; chmod +x /tmp/jsx;
RUN /tmp/jsx configure -s --no-sshagent;

CMD . /sandbox/env.sh && kosmos "j.servers.threebot.start(with_shell=False)"

EXPOSE 80 443


