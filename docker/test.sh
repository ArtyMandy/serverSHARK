#!/bin/bash

#first = mysqlpw

service mysql start
mysql -e "CREATE DATABASE IF NOT EXISTS servershark CHARACTER SET utf8 COLLATE utf8_general_ci;"

service mongodb start
mongo --eval "db.getSiblingDB('smartshark').createUser({user:'root', pwd:'$1',roles:[{role:'dbOwner', db:'smartshark'}]})"

echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin, 'admin@example.com', 'CHANGEME')" | python manage.py shell


cd /srv/www/serverSHARK
echo "environment started"
python3 -m venv .
source bin/activate
echo "start install wheel"
pip install wheel
pip install --no-cache-dir -r requirements.txt
pip install django-progressbarupload
echo "start copy settings"
cp /srv/www/serverSHARK/server/settings_template_vagrant.py /srv/www/serverSHARK/server/settings.py
cp /srv/www/serverSHARK/server/settings_template_vagrant.py ~/settings.py
#chmod +x ~/settings.py
#chmod +x /root/srv/www/serverSHARK/settings.py

mkdir -p /srv/www/serverSHARK/media/uploads/plugins
source bin/activate

echo "start redis install"
pip install redis
echo "start django server"
python manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'CHANGEME')" | python manage.py shell

python manage.py runserver --settings=server.settings 0.0.0.0:8000
