import Users

import os
import re

import hmac
import json

import time

import webapp2
import jinja2

from google.appengine.api import memcache
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = False)

secret = 'fart'




#-------------
#Magic Here

#-------------









# -----------------
# USER INSTRUCTIONS
#
# Write a function in the class robot called move()
#
# that takes self and a motion vector (this
# motion vector contains a steering* angle and a
# distance) as input and returns an instance of the class
# robot with the appropriate x, y, and orientation
# for the given motion.
#
# *steering is defined in the video
# which accompanies this problem.
#
# For now, please do NOT add noise to your move function.
#
# Please do not modify anything except where indicated
# below.
#
# There are test cases which you are free to use at the
# bottom. If you uncomment them for testing, make sure you
# re-comment them before you submit.
#import numpy as np
#
#from pylab import *
from math import *
import random

#import matplotlib.pyplot as plt
#from matplotlib.lines import Line2D
#import matplotlib.animation as animation
# --------
# 
# the "world" has 4 landmarks.
# the robot's initial coordinates are somewhere in the square
# represented by the landmarks.
#
# NOTE: Landmark coordinates are given in (y, x) form and NOT
# in the traditional (x, y) format!




steering_noise    = 0.1
distance_noise    = 0.01
measurement_noise = 0.1

weight_data       = 0.1
weight_smooth     = 0.2
p_gain            = 3.358
d_gain            = 6.681
i_gain            = 0.03125


SNAPSHOT_INTERVAL = 1

class plan:

    # --------
    # init: 
    #    creates an empty plan
    #

    def __init__(self, grid, init, goal, cost = 1):
        self.cost = cost
        self.grid = grid
        self.init = init
        self.goal = goal
        self.make_heuristic(grid, goal, self.cost)
        self.path = []
        self.spath = []

    # --------
    #
    # make heuristic function for a grid
        
    def make_heuristic(self, grid, goal, cost):
        self.heuristic = [[0 for row in range(len(grid[0]))] 
                          for col in range(len(grid))]
        for i in range(len(self.grid)):    
            for j in range(len(self.grid[0])):
                self.heuristic[i][j] = abs(i - self.goal[0]) + \
                    abs(j - self.goal[1])



    # ------------------------------------------------
    # 
    # A* for searching a path to the goal
    #
    #

    def astar(self,goal):


        if self.heuristic == []:
            raise ValueError, "Heuristic must be defined to run A*"

        # internal motion parameters
        delta = [[-1,  0], # go up
                 [ 0,  -1], # go left
                 [ 1,  0], # go down
                 [ 0,  1]] # do right


        # open list elements are of the type: [f, g, h, x, y]

        closed = [[0 for row in range(len(self.grid[0]))] 
                  for col in range(len(self.grid))]
        action = [[0 for row in range(len(self.grid[0]))] 
                  for col in range(len(self.grid))]

        closed[self.init[0]][self.init[1]] = 1


        x = self.init[0]
        y = self.init[1]
        h = self.heuristic[x][y]
        g = 0
        f = g + h

        open = [[f, g, h, x, y]]

        found  = False # flag that is set when search complete
        resign = False # flag set if we can't find expand
        count  = 0


        while not found and not resign:

            # check if we still have elements on the open list
            if len(open) == 0:
                resign = True
                
                
            else:
                # remove node from list
                open.sort()
                open.reverse()
                next = open.pop()
                x = next[3]
                y = next[4]
                g = next[1]

            # check if we are done

            if x == goal[0] and y == goal[1]:
                found = True
                # print '###### A* search successful'

            else:
                # expand winning element and add to new open list
                for i in range(len(delta)):
                    x2 = x + delta[i][0]
                    y2 = y + delta[i][1]
                    if x2 >= 0 and x2 < len(self.grid) and y2 >= 0 \
                            and y2 < len(self.grid[0]):
                        if closed[x2][y2] == 0 and self.grid[x2][y2] == 0:
                            g2 = g + self.cost
                            h2 = self.heuristic[x2][y2]
                            f2 = g2 + h2
                            open.append([f2, g2, h2, x2, y2])
                            closed[x2][y2] = 1
                            action[x2][y2] = i

            count += 1

        # extract the path



        invpath = []
        x = self.goal[0]
        y = self.goal[1]
        invpath.append([x, y])
        while x != self.init[0] or y != self.init[1]:
            x2 = x - delta[action[x][y]][0]
            y2 = y - delta[action[x][y]][1]
            x = x2
            y = y2
            invpath.append([x, y])

        self.path = []
        for i in range(len(invpath)):
            self.path.append(invpath[len(invpath) - 1 - i])




    # ------------------------------------------------
    # 
    # this is the smoothing function
    #

  


    def smooth(self, weight_data = 0.1, weight_smooth = 0.1, 
               tolerance = 0.000001):

        if self.path == []:
            raise ValueError, "Run A* first before smoothing path"

        self.spath = [[0 for row in range(len(self.path[0]))] \
                           for col in range(len(self.path))]
        for i in range(len(self.path)):
            for j in range(len(self.path[0])):
                self.spath[i][j] = self.path[i][j]

        change = tolerance
        while change >= tolerance:
            change = 0.0
            for i in range(1, len(self.path)-1):
                for j in range(len(self.path[0])):
                    aux = self.spath[i][j]
                    
                    self.spath[i][j] += weight_data * \
                        (self.path[i][j] - self.spath[i][j])
                    
                    self.spath[i][j] += weight_smooth * \
                        (self.spath[i-1][j] + self.spath[i+1][j] 
                         - (2.0 * self.spath[i][j]))
                    if i >= 2:
                        self.spath[i][j] += 0.5 * weight_smooth * \
                            (2.0 * self.spath[i-1][j] - self.spath[i-2][j] 
                             - self.spath[i][j])
                    if i <= len(self.path) - 3:
                        self.spath[i][j] += 0.5 * weight_smooth * \
                            (2.0 * self.spath[i+1][j] - self.spath[i+2][j] 
                             - self.spath[i][j])
                
            change += abs(aux - self.spath[i][j])
                






# ------------------------------------------------
# 
# this is the robot class
#

class robot:

    # --------
    # init: 
    #	creates robot and initializes location/orientation to 0, 0, 0
    #

    def __init__(self, length = 0.35):
        self.x = 0.0
        self.y = 0.0
        self.orientation = 0.0
        self.length = length
        self.steering_noise    = 0.0
        self.distance_noise    = 0.0
        self.measurement_noise = 0.0
        self.num_collisions    = 0
        self.num_steps         = 0

    # --------
    # set: 
    #	sets a robot coordinate
    #

    def set(self, new_x, new_y, new_orientation):

        self.x = float(new_x)
        self.y = float(new_y)
        self.orientation = float(new_orientation) % (2.0 * pi)


    # --------
    # set_noise: 
    #	sets the noise parameters
    #

    def set_noise(self, new_s_noise, new_d_noise, new_m_noise):
        # makes it possible to change the noise parameters
        # this is often useful in particle filters
        self.steering_noise     = float(new_s_noise)
        self.distance_noise    = float(new_d_noise)
        self.measurement_noise = float(new_m_noise)

    # --------
    # check: 
    #    checks of the robot pose collides with an obstacle, or
    # is too far outside the plane

    def check_collision(self, grid):
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == 1:
                    dist = sqrt((self.x - float(i)) ** 2 + 
                                (self.y - float(j)) ** 2)
                    if dist < 0.5:
                        self.num_collisions += 1
                        return False
        return True
        
    def check_goal(self, goal, threshold = .25):
        dist =  sqrt((float(goal[0]) - self.x) ** 2 + (float(goal[1]) - self.y) ** 2)
        return dist < threshold
        
    # --------
    # move: 
    #    steering = front wheel steering angle, limited by max_steering_angle
    #    distance = total distance driven, most be non-negative

    def move(self, grid, steering, distance, 
             tolerance = 0.001, max_steering_angle = pi / 4.0):

        if steering > max_steering_angle:
            steering = max_steering_angle
        if steering < -max_steering_angle:
            steering = -max_steering_angle
        if distance < 0.0:
            distance = 0.0


        # make a new copy
        res = robot()
        res.length            = self.length
        res.steering_noise    = self.steering_noise
        res.distance_noise    = self.distance_noise
        res.measurement_noise = self.measurement_noise
        res.num_collisions    = self.num_collisions
        res.num_steps         = self.num_steps + 1

        # apply noise
        steering2 = random.gauss(steering, self.steering_noise)
        distance2 = random.gauss(distance, self.distance_noise)


        # Execute motion
        turn = tan(steering2) * distance2 / res.length

        if abs(turn) < tolerance:

            # approximate by straight line motion

            res.x = self.x + (distance2 * cos(self.orientation))
            res.y = self.y + (distance2 * sin(self.orientation))
            res.orientation = (self.orientation + turn) % (2.0 * pi)

        else:

            # approximate bicycle model for motion

            radius = distance2 / turn
            cx = self.x - (sin(self.orientation) * radius)
            cy = self.y + (cos(self.orientation) * radius)
            res.orientation = (self.orientation + turn) % (2.0 * pi)
            res.x = cx + (sin(res.orientation) * radius)
            res.y = cy - (cos(res.orientation) * radius)

        # check for collision
        # res.check_collision(grid)

        return res

    # --------
    # sense: 
    #    

    def sense(self):

        return [random.gauss(self.x, self.measurement_noise),
                random.gauss(self.y, self.measurement_noise)]

    # --------
    # measurement_prob
    #    computes the probability of a measurement
    # 

    def measurement_prob(self, measurement):

        # compute errors
        error_x = measurement[0] - self.x
        error_y = measurement[1] - self.y

        # calculate Gaussian
        error = exp(- (error_x ** 2) / (self.measurement_noise ** 2) / 2.0) \
            / sqrt(2.0 * pi * (self.measurement_noise ** 2))
        error *= exp(- (error_y ** 2) / (self.measurement_noise ** 2) / 2.0) \
            / sqrt(2.0 * pi * (self.measurement_noise ** 2))

        return error



    def __repr__(self):
        # return '[x=%.5f y=%.5f orient=%.5f]'  % (self.x, self.y, self.orientation)
        return '[%.5f, %.5f]'  % (self.x, self.y)





# ------------------------------------------------
# 
# this is the particle filter class
#

class particles:

    # --------
    # init: 
    #	creates particle set with given initial position
    #

    def __init__(self, x, y, theta, 
                 steering_noise, distance_noise, measurement_noise, N = 100):
        self.N = N
        self.steering_noise    = steering_noise
        self.distance_noise    = distance_noise
        self.measurement_noise = measurement_noise
        
        self.data = []
        for i in range(self.N):
            r = robot()
            r.set(x, y, theta)
            r.set_noise(steering_noise, distance_noise, measurement_noise)
            self.data.append(r)


    # --------
    #
    # extract position from a particle set
    # 
    
    def get_position(self):
        x = 0.0
        y = 0.0
        orientation = 0.0

        for i in range(self.N):
            x += self.data[i].x
            y += self.data[i].y
            # orientation is tricky because it is cyclic. By normalizing
            # around the first particle we are somewhat more robust to
            # the 0=2pi problem
            orientation += (((self.data[i].orientation
                              - self.data[0].orientation + pi) % (2.0 * pi)) 
                            + self.data[0].orientation - pi)
        return [x / self.N, y / self.N, orientation / self.N]

    # --------
    #
    # motion of the particles
    # 

    def move(self, grid, steer, speed):
        newdata = []

        for i in range(self.N):
            r = self.data[i].move(grid, steer, speed)
            newdata.append(r)
        self.data = newdata

    # --------
    #
    # sensing and resampling
    # 

    def sense(self, Z):
        w = []
        for i in range(self.N):
            w.append(self.data[i].measurement_prob(Z))

        # resampling (careful, this is using shallow copy)
        p3 = []
        index = int(random.random() * self.N)
        beta = 0.0
        mw = max(w)

        for i in range(self.N):
            beta += random.random() * 2.0 * mw
            while beta > w[index]:
                beta -= w[index]
                index = (index + 1) % self.N
            p3.append(self.data[index])
        self.data = p3

    



    

# --------
#
# run:  runs control program for the robot
#
def run2(grid, goal, spath, params, printflag = False, speed = 0.3, timeout = 500):
    
    myrobot = robot()

    myrobot.set(0., 0., 0.)
    myrobot.set_noise(steering_noise, distance_noise, measurement_noise)
    filter = particles(myrobot.x, myrobot.y, myrobot.orientation,
                       steering_noise, distance_noise, measurement_noise)

    cte  = 0.0
    err  = 0.0
    N    = 0

    index = 0 # index into the path
    
    x = vectorizepath(spath)
    
    tail = x[0]
    vect = x[2]
    integ_cte = 0.0
    max_cte = 0
    d = {}
    
    while not myrobot.check_goal(goal) and N < timeout:

        diff_cte = - cte


        # ----------------------------------------
        # compute the CTE

        # start with the present robot estimate

        x = myrobot.x
        y = myrobot.y
        theta = myrobot.orientation
        d[N] = {'x': round(x,2), 'y': round(y,2), 'theta': round(theta,2)}
        rx = x - tail[index][0]
        ry = y - tail[index][1]
        
        dx = vect[index][0]
        dy = vect[index][1]
        
        mu = (rx*dx +ry*dy)/(dx**2 + dy**2)
        
        if (mu > 1):
            if not(index + 1 >= len(vect)):
                index += 1
        
        cte = (ry*dx -rx*dy)/(dx**2 + dy**2)

        ### ENTER CODE HERE
        

        # ----------------------------------------


        diff_cte += cte
        integ_cte += cte
        if abs(cte) < 0.0001:
            steer = 0
        else:
            steer = - params[0] * cte - params[1] * diff_cte - params[2] * integ_cte
            
        if (diff_cte > .02):
            speed = 0.07
        if (diff_cte > .06):
            speed = 0.05
        if (diff_cte < .0005 and integ_cte < .004 and speed < .1):
            speed *= 1.1
            

        myrobot = myrobot.move(grid, steer, speed)
        filter.move(grid, steer, speed)


        
        max_cte += abs(cte)
#            print(max_cte)
        
        
        Z = myrobot.sense()
        filter.sense(Z)

#        if not myrobot.check_collision(grid):
#            print '##### Collision ####'

        err += (cte ** 2)
        N += 1

        if printflag:
            print myrobot, cte, index, d[N-1]

    #robotart.plotmotion(spath, ([xl,yl]))

    return [myrobot.check_goal(goal), myrobot.num_collisions, myrobot.num_steps, max_cte, d]



# ------------------------------------------------
# 
# this is our main routine
#




    
def vectorizepath(spath):
    testpath = []
    for i in range(len(spath)):
        testpath.append(spath[i])
    
    hold = testpath.pop(0)
    tails = []
    heads = []
    vects = []
    i = 0
    while (testpath):
        tails.append(hold)
        heads.append(testpath.pop(0))
        
       
        
        vects.append([heads[i][0]-tails[i][0],heads[i][1]-tails[i][1]])
        #print(str.format("tail({0[0]:.2f}, {0[1]:.2f}) and head({1[0]:.2f}, {1[1]:.2f}) and vects({2[0]:.2f}, {2[1]:.2f})", tails[i], heads[i], vects[i]))
        hold = heads[i]
        i+=1
    return [tails, heads, vects]


def main(grid, init, goal, steering_noise, distance_noise, measurement_noise, 
     weight_data, weight_smooth, p_gain, d_gain, i_gain):

    path = plan(grid, init, goal)
    path.astar(goal)
    path.smooth(weight_data, weight_smooth)

    
    
    """    
    ## shows how vectorized path works.     
        
    #    x = vectorizepath(path)
    #    
    #    tai = x[0]
    #    hea = x[1]
    #    vec = x[2]
    #    for i in range(len(tai)):
    #        print(str.format("tail({0[0]:.2f}, {0[1]:.2f}) and head({1[0]:.2f}, {1[1]:.2f}) and vects({2[0]:.2f}, {2[1]:.2f})", tai[i], hea[i], vec[i]))
    """
    
    #testdot()
    

    
    return (run2(grid, goal, path.spath, [p_gain, d_gain, i_gain], True))

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

    def as_dict(self):
        time_fmt = '%c'
        d = {'subject': self.subject,
             'content': self.content,
             'created': self.created.strftime(time_fmt),
             'last_modified': self.last_modified.strftime(time_fmt)}
        return d

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class BlogHandler(webapp2.RequestHandler):
         
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and Users.User.by_id(int(uid))

        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'
    
    def set_posts(self, key, post_id = None):
        timenow = time.time()
        
        if post_id:
            postinfo = db.Key.from_path('Post', int(post_id), parent=blog_key())
            data = db.get(postinfo)
        else:
            data = Post.all().order('-created')
        
            
        memcache.delete(key)
        memcache.add(key, [data, timenow])
        
        return [data, 0]
    
    def get_posts(self, key, post_id = None):
        data = memcache.get(key)
        
        if data is not None:
            return data
        else:
            data = self.set_posts(key, post_id)
            return data
            
    def flush(self):
        memcache.flush_all()


##### user stuff

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError



class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = Users.User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = Users.User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/wiki/welcome')

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = Users.User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/wiki/welcome')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/wiki/signup')

class Blah(BlogHandler):
    def get(self):
        n = self.request.get("name")
        if not n:
            n = ""
        self.render('newish.html', name = "")
        
    def post(self):
        n = self.request.get("name")
        m = json.loads(n);
        self.write(m[1][1])
        
        
        self.render('newish.html', name = json.dumps(m))
        


class Test(BlogHandler):
    def get(self):
        n = self.request.get("name")
        if not n:
            n = ""
        self.render('test.html', name = "")
        
    def post(self):
        n = self.request.get("name")


        grid = json.loads(n)


        init = [0, 0]
        goal = [len(grid)-1, len(grid[0])-1]
    
        d = main (grid, init, goal, steering_noise, distance_noise, measurement_noise, 
           weight_data, weight_smooth, p_gain, d_gain, i_gain)[4]
        
        dump = json.dumps(d)

        self.render('gridval.html', name = dump)
        
        
class HomePage(BlogHandler):
    def get(self):
        grid = [[0, 1, 0, 0, 0, 0],
                [0, 1, 0, 1, 1, 0],
                [0, 0, 0, 1, 0, 0],
                [1, 1, 1, 1, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 0],
                [0, 1, 0, 0, 0, 1],
                [0, 1, 0, 1, 0, 1],
                [0, 0, 0, 1, 0, 1],
                [0, 1, 0, 1, 0, 0]]


        init = [0, 0]
        goal = [len(grid)-1, len(grid[0])-1]
    
        d = main (grid, init, goal, steering_noise, distance_noise, measurement_noise, 
           weight_data, weight_smooth, p_gain, d_gain, i_gain)[4]
        
        grids = json.dumps(grid)

        path = json.dumps(d) 

        
        self.render('foobar.html', jsonStr = path, blocks = grids)

#lx = myrobot.linesx
#ly = myrobot.linesy
#
#fig = plt.figure()
#ax = fig.add_subplot(111, autoscale_on=False, xlim=(-100, 150), ylim=(-100, 150))
#ax.grid()
#linefr, = ax.plot([], [], lw=1)
#linefl, = ax.plot([], [], lw=1)
#linebr, = ax.plot([], [], lw=1)
#linebl, = ax.plot([], [], lw=1)
#linebod, = ax.plot([], [], lw=1)
#
#def init():
#    linefr.set_data([], [])
#    linefl.set_data([], [])
#    linebr.set_data([], [])
#    linebl.set_data([], [])
#    linebod.set_data([], [])
#    return linefr, linefl, linebr, linebl, linebod
#
#def animate(i):
#    linefr.set_data(lx[0][i], ly[0][i])
#    linefl.set_data(lx[1][i], ly[1][i])
#    linebr.set_data(lx[2][i], ly[2][i])
#    linebl.set_data(lx[3][i], ly[3][i])
#    linebod.set_data(lx[4][i], ly[4][i])
#
#    return linefr, linefl, linebr, linebl, linebod
#    
#for i in range(1, T):
#    ani = animation.FuncAnimation(fig, animate, np.arange(1, T), interval=1)    
#
##ani.save('test_sub.mp4')
#
#plt.show()
## IMPORTANT: You may uncomment the test cases below to test your code.
## But when you submit this code, your test cases MUST be commented
## out. Our testing program provides its own code for testing your
## move function with randomized motion data.




        
    def post(self):
        self.render('clock.html')


app = webapp2.WSGIApplication([('/wiki/signup', Register),
                               ('/wiki/login', Login),
                               ('/wiki/logout', Logout),
                               ('/test', Test),
                               ('/', HomePage),
                               ('/blah', Blah)
                               ],
                              debug=True)
