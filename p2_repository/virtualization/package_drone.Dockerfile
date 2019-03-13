FROM ubuntu:16.04

MAINTAINER James O'Carroll <james.ocarroll@stackhead.com>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    add-apt-key \
    software-properties-common

# Install OpenJDK 8
RUN apt-get install -y \
    openjdk-8-jre-headless \
    vim

# Add Package Drone signing key (from keyserver.ubuntu.com)
RUN add-apt-key -k keyserver.ubuntu.com 320E6224

# Add the Package Drone repository
RUN add-apt-repository "deb http://download.eclipse.org/package-drone/release/current/ubuntu package-drone default" && apt-get update

# Update index and install Package Drone
RUN apt-get install -y org.eclipse.packagedrone.server

# By default, channels show at most 10000 artifacts (including child artifacts).  Channels with more artifacts than this will display an error message.
# Modify system properties in a config file to increase the number of artifacts that can be shown.
RUN sed -i 's/# JAVA_OPTS=""/JAVA_OPTS="$JAVA_OPTS -Ddrone.web.maxListSize=20000"/g' /etc/default/package-drone-server

EXPOSE 8080

CMD ["/usr/lib/package-drone-server/instance/server"]

