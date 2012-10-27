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
import urllib
import cgi
import re
import os
import jinja2
import unit3

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")                        
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def escape_html(name):
        return cgi.escape(name, quote = True)

months = ['January',
          'February',
          'March',
          'April',
          'May',
          'June',
          'July',
          'August',
          'September',
          'October',
          'November',
          'December']
month_abbvs = dict((m[:3].lower(), m) for m in months)    

email_endings = ['com',
                 'gov',
                 'google']
                 
def Cypher13(str2shift):
    newstr = ""
    for i in range(len(str2shift)):
        
        inter = (ord(str2shift[i]))

        if (inter > 64 and inter < 91):
            inter -= 65
            inter = ((inter + 13) % 26)+65
            
        if (inter > 96 and inter < 123):
            inter -= 97
            inter = ((inter + 13) % 26)+97

        newstr = '{0}{1}'.format(newstr, (chr(inter)))

    return (newstr)



def valid_username(username):

    return USER_RE.match(username)

def valid_email(email):
    if EMAIL_RE.match(email):
        return(True)

    return (False)

def valid_password(pass1, pass2):
    
    if (pass1 == pass2):
        if PASS_RE.match(pass1):
            
            return 0
        else:
            return 1
    else:
        return 2

def valid_month(month):
    if month:
        short_month = month[:3].lower()
        return month_abbvs.get(short_month)
            
    
    return short_month

def valid_day(day):
    if day and day.isdigit():
        num_day = int(day)
        
        if (num_day < 1 or num_day > 31):
            num_day = None
            
    else:
        num_day = None
    
    return num_day

def valid_year(year):
    if year and year.isdigit():
        num_year = int(year)
        
        if (num_year < 1900 or num_year > 2020):
            num_year = None
            
    else:
        num_year = None
    
    return num_year


form="""
<form method="post">
	What is your birthday?
	<br>
	<label>
         Month
		<input type="text" name="month" value="%(month)s">
	</label>
	
	<label> 
         Day
		<input type="text" name="day" value="%(day)s">
	</label>
	<label> 
         Year
		<input type="text" name="year" value="%(year)s">
	</label>
 
     <div style="color: red">%(error)s</div>
	
	<br>
	<br>
	
	<input type="submit">
</form>
"""



def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)


class MainHandler(webapp2.RequestHandler):
    def write_form(self, error="", month="", day="", year=""):
        self.response.out.write(form % {"error": error, 
                                        "month": escape_html(month),
                                        "day": escape_html(day), 
                                        "year": escape_html(year)})
        
    def get(self):
        self.write_form()
        
    def post(self):
        month = (self.request.get('month'))
        day = (self.request.get('day'))
        year = (self.request.get('year'))
        
        
        user_month = valid_month(month)
        user_day = valid_day(day)
        user_year = valid_year(year)
        
        if not (user_month and user_day and user_year):
            self.write_form("That doesn't look valid to me, friend.",month, day, year)
        else:
            self.redirect("/thanks")

class ThanksHandler(BaseHandler):
       
    def get(self):
        username = self.request.get('username')
        if (valid_username(username)):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/unit2/test')
    

        

class CypherHandler(BaseHandler):
    def get(self):
        self.render('CS253 Hw2-1.html')
        
    def post(self):
        CT = ''
        text = (self.request.get('text'))
        if text:
            text = Cypher13(text)
        CT = text.encode('ascii')

        self.render('CS253 Hw2-1.html', cyphertext = CT)


class TestHandler(BaseHandler):
        
    def get(self):
        self.render('CS253 Hw2-2.html')
    
    def post(self):
        uname = self.request.get('username')
        origpwd = self.request.get('password')
        repeatpwd = self.request.get('verify')
        email = self.request.get('email')
        
        errorflag = False        
        
        
        params = dict()
        
        pwcheck = valid_password(origpwd, repeatpwd)
        
        if pwcheck == 2:
            params['PasswordRepeatError'] = "Error, your passwords don't match."
            errorflag = True
        elif pwcheck == 1:
            params['PasswordOrigError'] = "Error, your passwords isn't valid."
            errorflag = True
            
        if email:
            if not(valid_email(email)):
                params['EmailError'] = "Error, your email isn't valid."
                params['email'] = email
                errorflag = True
            else:
                params['email'] = email

        
        
        if not(uname):
            params['UserNameError'] = "Error, you must enter a user name."
            errorflag = True
            uname = ""
        elif not(valid_username(uname)):
            params['UserNameError'] = "Error, you must enter a VALID user name."
            params['username'] = uname
            errorflag = True
        else:
            params['username'] = uname
        
        
        if errorflag: 
            self.render('CS253 Hw2-2.html', **params)
        else:
            self.redirect('/thanks?username=' + uname)


app = webapp2.WSGIApplication([('/', MainHandler), 
                               ('/thanks', ThanksHandler),
                               ('/unit2/cypher', CypherHandler),
                                ('/unit2/test',TestHandler),
                                ('/blah', unit3.Unit3Handler)],
                              debug=True)
