#!/usr/bin/env python

from __future__ import unicode_literals
from django.contrib.auth.models import User

districts = ['Nkhatabay', 'Nkhotakota', 'Machinga', 'Mulanje', 'Kasungu', 'Nsanje']

for d in districts:
	User.objects.create_user(d+'DP','',d+'1')
        User.objects.create_user(d+'IM','',d+'2')
