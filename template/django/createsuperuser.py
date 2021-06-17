#!/usr/bin/env python
import os
import sys


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()


from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()

email = sys.argv[1]  # "{c.config.django.superuser.email}"
password = sys.argv[2]  # "{c.config.django.superuser.password}"
username = sys.argv[3]  # "{c.config.django.superuser.username}"

user = dict(password=password)
if User.username:
    user['username'] = username
if User.email:
    user['email'] = email

try:
    User.objects.create_superuser(**user)
except Exception as e:
    print(e)
    print("Superuser already exsits:", email)
