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

import os
import jinja2

import random
import string
import hashlib
import hmac

import re

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def hash_str(s):
    SECRET = "SuperSecretText"
    return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
    sp = h.split("|")
    if (len(sp) == 2):
        check = hash_str(sp[0])
        if check == sp[1]:
            return (sp[0])
    return None

    
def make_pw_hash(name, pw):
    salt = make_salt()
    hashd = hash_str(name+pw)
    h = hashlib.sha256(hashd + salt).hexdigest()
    return ('%s|%s' % (h, salt))

def valid_pw(name, pw, h):
    x = h.split('|')
    hashv = x[0] 
    salt = x[1]
    hashd = hash_str(name+pw)
    h = hashlib.sha256(hashd + salt).hexdigest()
    if h == hashv:
        return True
    
    return False

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

class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)    
    
class Blog(db.Model):
    title = db.StringProperty(required = True)
    blogtext = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)  

class User(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    email = db.StringProperty(required = False)  
    first = db.StringProperty(required = False)
    last = db.StringProperty(required = False)

class MainHandler(BaseHandler):
    def render_front(self, title="", art="", error=""):
        arts = db.GqlQuery("SELECT * FROM Art "
                            "ORDER BY created DESC")
        
        self.render("front.html", title=title, art=art, error=error, arts = arts)
        
    
    def get(self):
        self.render_front()
    
    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")
        
        if title and art:
            a = Art(title = title, art = art)
            a.put()
            
            self.redirect("/")
        else:
            error = "we need both a title and some artwork!"
            self.render_front(title, art, error)


class BlogHandler(BaseHandler):
    def render_blog(self, title="", art="", error=""):
        blogs = db.GqlQuery("SELECT * FROM Blog "
                            "ORDER BY created DESC")
        
        self.render("Blog.html", blogs = blogs)
        
    
    def get(self):
        self.render_blog()
    
#    def post(self):
#        title = self.request.get("title")
#        art = self.request.get("art")
#        
#        if title and art:
#            a = Art(title = title, art = art)
#            a.put()
#            
#            self.redirect("/")
#        else:
#            error = "we need both a title and some artwork!"
#            self.render_front(title, art, error)
            
class NewPostHandler(BaseHandler):
    
    def render_new_post(self, title="", blogtext="", error=""):
        
        self.render("NewPost.html", title=title, blogtext=blogtext, error=error)
        
    
    def get(self):
        self.render_new_post()
    
    def post(self):
        title = self.request.get("subject")
        blogtext = self.request.get("content")
        
        if title and blogtext:
            b = Blog(title = title, blogtext = blogtext)
            b.put()
            idnum = b.key().id()
            
            self.redirect("/blog/" + str(idnum))
        else:
            error = "we need both a title and some artwork!"
            self.render_new_post(title, blogtext, error)

class IndvPostHandler(BaseHandler):
       
    
    def get(self, num):
        blog = Blog.get_by_id(int(num))
        if (blog):
            self.write(blog.title)
        else:
            self.write("that didn't work")
            
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)
    
def username_taken(username):
    return db.GqlQuery("SELECT * FROM User WHERE ANCESTOR IS :2 AND username =  :1", username, blog_key() ).get()

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)
    
class SignIn(BaseHandler):
    
    def render_SignIn(self, uName="", uEmail="", error_username="", error_password="", error_verify="", error_email=""):
        
        self.render("Register.html", uName=uName, email=uEmail, error_username=error_username, error_password=error_password, error_verify=error_verify, error_email=error_email)
        
    
    def get(self):
        self.render_SignIn()
    
    def post(self):
        uName  = self.request.get("username")
        uPass  = self.request.get("password")
        verify = self.request.get("verify")
        uEmail = self.request.get("email")

        have_error = False
        
        params = dict(uName = uName,
                      uEmail = uEmail)

        if not valid_username(uName):
            params['error_username'] = "That's not a valid username."
            have_error = True
        elif username_taken(uName):
            params['error_username'] = "That username is already taken!"
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
            
            uPass = make_pw_hash(uName, uPass)
            U = User(parent = blog_key(), username = uName, password = uPass, email = uEmail)
            U.put()
            idnum = U.key().id()
            idnum = make_secure_val(str(idnum))
            cook = str.format('UserID={0}; Path=/', idnum)
            self.response.headers.add_header('Set-Cookie', cook)
                        
            self.redirect('/blog/welcome' + "?UserID=" + idnum)
        


class UserHome(BaseHandler):
    
    def render_UserHome(self, uName="", uEmail=""):
        
        self.render("UserHome.html", uName=uName, uEmail=uEmail)
        
    
    def get(self):
        
        UserID = self.request.cookies.get('UserID')
        UserID = check_secure_val(UserID)
        if UserID:
            key = db.Key.from_path('User', int(UserID), parent=blog_key())
            user = db.get(key)        
            self.response.write(user)
            self.render_UserHome(user.username, user.email)
        else: 
            self.redirect('/blog/signup')
        
        

class LogIn(BaseHandler):
    
    def render_LogIn(self, uName="", error_username = ""):
        
        self.render("Login.html", uName=uName, error_username=error_username)
        
    
    def get(self):
        self.render_LogIn()

    def post(self):
        uName  = self.request.get("username")
        uPass  = self.request.get("password")
            

        params = dict(uName = uName)     
        have_error = True
        
        if  not valid_username(uName) or not username_taken(uName):
            have_error = True
        else:
            user = db.GqlQuery("SELECT * FROM User WHERE ANCESTOR IS :2 AND username =  :1", uName, blog_key() ).get()
            #for user in users:
            if  valid_pw(uName, uPass, user.password):
                have_error = False
                uid = user.key().id()
        
        
        if have_error:
            params['error_username'] = "There was an error with your login."
            self.render_LogIn(**params)
        else:
            uid = make_secure_val(str(uid))
            cook = str.format('UserID={0}; Path=/', uid)
            self.response.headers.add_header('Set-Cookie', cook)
                        
            self.redirect('/blog/welcome' + "?UserID=" + str(uid))

class LogOut(BaseHandler):
 
    def get(self):
        
        self.response.headers.add_header('Set-Cookie', 'UserID=; Path=/')
        self.redirect('/blog/signup')    
        

app = webapp2.WSGIApplication([('/', MainHandler),
                                ('/blog', BlogHandler),
                                ('/blog/newpost', NewPostHandler),
                                ('/blog/(\d+)', IndvPostHandler),
                                ('/blog/signup', SignIn),
                                ('/blog/login', LogIn),
                                ('/blog/logout', LogOut),
                                ('/blog/welcome', UserHome)],
                              debug=True)
