FROM ubuntu:18.04

EXPOSE 8000
EXPOSE 27017

RUN   apt-get update && \
      apt-get install -y \
      git \
      python3-venv \
      python-pip \
      python3-cffi \
      libgit2-26 \
      libgit2-dev \
      libmysqlclient-dev \
      libssl-dev \
      python3-setuptools \
      rpm \
      build-essential \
      libtool \
      pkg-config \
      autoconf \
      python3-dev \
      libffi-dev \
      redis-server \
      cmake

RUN apt-get install -y mongodb mysql-server

ENV MYSQLPASSWORD="CHANGEME"
#RUN service mysql start
#mysql -u root --password=

#RUN debconf-set-selections <<< 'mysql-server mysql-server/root_password password ${MYSQLPASSWORD}'
#RUN debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password ${MYSQLPASSWORD}'

RUN mkdir -p /srv/www
WORKDIR /srv/www

RUN git clone https://github.com/ArtyMandy/serverSHARK.git

WORKDIR /srv/www/serverSHARK


RUN pip install --upgrade pip

#COPY /srv/www/serverSHARK/server/settings_template_vagrant.py /srv/www/serverSHARK/server/settings.py
#COPY /srv/www/serverSHARK/server/settings_template_vagrant.py ~/

COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
RUN pwd

ENTRYPOINT /docker-entrypoint.sh ${MYSQLPASSWORD}
