# About

Video Game Catalog allows users to log in using their Google account to contribute to 
a catalog of video games.  Video Games are categorized by genre.  Box art upload is not 
available in this version and will be added at a later time.

# Install

Make sure you have all of the following libraries installed:

```
import random
import string
import json
import httplib2
import requests
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Games
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask import session as login_session
from flask import make_response
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
```

then run ```python database_setup.py``` to create the empty database videogames.db and 
```python application.py``` from the catalog directory to start the site.  Go to your 
browser and visit http://localhost:5000 to see the home page and login.

# How to use

Click the Google Sign-in button to log in using an existing Google account or to create one.
This credential is what will allow you to add genres and video games accordingly.
You must allow this site to access your Google account.  This site collects your
Google email address, Google user ID, Google profile picture, name and username as it is saved in
Google.  Information used on this site is secure and will not be used in any way other than
protecting the data you enter on this site.

# Development

Video Game Catalog is a Python project that uses Flask and SQLAlchemy.  Authentication is 
secured using oauth 2.0 and Google's services. 

## Libraries

- **Python 2.7.12**
- **Flask 0.9** - http://flask.pocoo.org
- **SQLAlchemy 1.1.11** - http://www.sqlalchemy.org
- **OAuth 2.0 Client** - http://github.com/google/oauth2client