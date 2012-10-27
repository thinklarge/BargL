#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2

import re
from string import letters

import os
import jinja2


from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__), 'Forms')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(self.render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
        
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)


class User(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    email = db.StringProperty(required = False)  
    first = db.StringProperty(required = False)
    last = db.StringProperty(required = False)
    
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)
    
class SignIn(BaseHandler):
    
    def render_SignIn(self, uName="", uEmail="", error_username="", error_password="", error_verify="", error_email=""):
        
        self.render("Register.html", uName=uName, uEmail=uEmail, error_username=error_username, error_password=error_password, error_verify=error_verify, error_email=error_email)
        
    
    def get(self):
        self.render_SignIn()
    
    def post(self):
        uPass = self.request.get("user_pass")
        uName = self.request.get("user_name")
        verify = self.request.get("verify")
        uEmail = self.request.get("user_email")

        have_error = False
        
        params = dict(uName = uName,
                      uEmail = uEmail)

        if not valid_username(uName):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(uPass):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif uPass != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(uEmail):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render_SignIn(**params)
        else:
            U = User(parent = blog_key(), username = uName, password = uPass, email = uEmail)
            U.put()
            self.redirect('/' )
            
        

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('Thanks for your registration.')

app = webapp2.WSGIApplication([('/', MainHandler),    ('/Blog/Registration', SignIn)],
                              debug=True)
