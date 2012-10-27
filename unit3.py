# -*- coding: utf-8 -*-
"""
Created on Mon Jul 02 16:32:18 2012

@author: elarge
"""

import webapp2
import cgi

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

def escape_html(name):
        return cgi.escape(name, quote = True)

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

class Unit3Handler(webapp2.RequestHandler):
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

app = webapp2.WSGIApplication([('/blah', Unit3Handler)],
                              debug=True)