FROM ubuntu:focal

RUN adduser steam
WORKDIR /home/steam

RUN echo steam steam/question select "I AGREE" | debconf-set-selections \
 && echo steam steam/license note '' | debconf-set-selections
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository multiverse && \
    dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y lib32gcc1 steamcmd locales && \
    rm -rf -- /var/cache/apt/archives/*

RUN locale-gen en_US.UTF-8
ENV LANG 'en_US.UTF-8'
ENV LANGUAGE 'en_US:en'

RUN ln -s /usr/games/steamcmd /usr/bin/steamcmd

USER steam

CMD steamcmd +login anonymous +force_install_dir SatisfactoryDedicatedServer +app_update 1690800 +quit && \
    echo "wait 5 seconds" && \
    sleep 5 && \
    /home/steam/.steam/steamcmd/SatisfactoryDedicatedServer/FactoryServer.sh -multihome=$(hostname -i) -NOSTEAM
