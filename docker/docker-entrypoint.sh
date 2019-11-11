#!/bin/bash

service mysql start
mysql -e "CREATE DATABASE IF NOT EXISTS servershark CHARACTER SET utf8 COLLATE utf8_general_ci;"

service mongodb start
mongo --eval "db.getSiblingDB('smartshark').createUser({user:'root', pwd:'$1',roles:[{role:'dbOwner', db:'smartshark'}]})"

ln -s /usr/bin/python3.6 /usr/bin/python3.5
cd /srv/www/serverSHARK

echo "python environment started"
python3 -m venv .
source bin/activate

echo "start install wheel"
pip install wheel
pip install --no-cache-dir -r requirements.txt
pip install django-progressbarupload

echo "start copy settings"
cp /srv/www/serverSHARK/server/settings_template_vagrant.py /srv/www/serverSHARK/server/settings.py
cp /srv/www/serverSHARK/server/settings_template_vagrant.py ~/settings.py


mkdir -p /srv/www/serverSHARK/media/uploads/plugins
source bin/activate

echo "start redis "
pip install redis
redis-server --daemonize yes
echo "start django migrate"
python manage.py migrate

echo "admin creation"
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'CHANGEME')" | python manage.py shell

echo "start django server"
python manage.py runserver 0.0.0.0:8000 &

echo "run peon"
source bin/activate
python manage.py peon
