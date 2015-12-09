# Introduction to Programming: Project 4
# By Earl S. Choi
import cgi
import urllib
import os

from google.appengine.api import users
from google.appengine.ext import ndb


import jinja2
import webapp2

# Set up jinja environment

template_dir = os.path.join(os.path.dirname(__file__), "templates")

# Instructor Notes:
# Suggest to print out template_dir to see how the file path is being constructured.
# You can find the print out in the Logs in Google App Engine (GAE). For Windows and Mac users,
# you need to click on the "Logs" button to be able to see the print messages

#print "###" # These hash marks helps us locate our print statement from the rest of the messages
              # Google App Engine gives us
#print template_dir
#print "###"

# For Windows Users, you need to add in a logging flag for GAE to print out your
# statements appropriately. Please go here to download the "Google App Engine Troubleshooting"
# guide to learn how to add in the logging flag:
# https://www.udacity.com/course/viewer#!/c-nd000/l-4166899177/m-3974308850
 


jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
      autoescape = True)

DEFAULT_WALL = 'Public'

# We set a parent key on the 'Post' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def wall_key(wall_name=DEFAULT_WALL):
  """Constructs a Datastore key for a Wall entity. (different wall entities: public, and?)

  We use wall_name as the key.
  """
  return ndb.Key('Wall', wall_name)

# These are the objects that will represent our Author and our Post. We're using
# Object Oriented Programming to create objects in order to put them in Google's
# Database. These objects inherit Googles ndb.Model class.
class Author(ndb.Model):
  """Sub model for representing an author."""
  identity = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=False)
  email = ndb.StringProperty(indexed=False)

class Post(ndb.Model):
  """A main model for representing an individual post entry."""
  author = ndb.StructuredProperty(Author)
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)


class Handler(webapp2.RequestHandler):
  """Initializes jinja environment"""
  def write(self, *a, **kw): #writes to browser
      self.response.out.write(*a, **kw)
  
  def render_str(self, template, **params): #get's string from template
    t = jinja_env.get_template(template)
    return t.render(params)
  
  def render(self, template, **kw): ## writes browser-friendly template
    self.write(self.render_str(template, **kw))

class MainPage(Handler):
  """main handler renders hompage with queried comments"""
  def get(self):
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    if wall_name == DEFAULT_WALL.lower(): wall_name = DEFAULT_WALL

    # Ancestor Queries, as shown here, are strongly consistent
    # with the High Replication Datastore. Queries that span
    # entity groups are eventually consistent. If we omitted the
    # ancestor from this query there would be a slight chance that
    # Greeting that had just been written would not show up in a
    # query.

    # [START query]
    posts_query = Post.query(ancestor = wall_key(wall_name)).order(-Post.date)

    # The function fetch() returns all posts that satisfy our query. The function returns a list of
    # post objects
    posts =  posts_query.fetch()
    # [END query]

    # If a person is logged into Google's Services
    user = users.get_current_user()
    if user:
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        user_name = user.nickname()
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
        user_name = 'Anonymous Poster'

"""How do I transfer this task to Jinja?
    # Create our posts html
    posts_html = ''
    # for post in posts:

    #   # Check if the current signed in user matches with the author's identity from this particular
    #   # post. Newline character '\n' tells the computer to print a newline when the browser is
    #   # is rendering our HTML
      if user and user.user_id() == post.author.identity:
        posts_html += '<div><h3>(You) ' + post.author.name + '</h3>\n'
      else:
        posts_html += '<div><h3>' + post.author.name + '</h3>\n'

      posts_html += 'wrote:' + cgi.escape(post.content) + '</blockquote>\n'
      posts_html += '</div>\n'
"""
    sign_query_params = urllib.urlencode({'wall_name': wall_name}) # wall_name was set above as ancestor key and in 'posts'
      # urllib.urlencode example: this is getting passed into the html template as 
      # >>> import urllib  
      # >>> dict = { 'First_Name' : 'Jack', 'Second_Name' : "West"}
      # >>> urllib.urlencode(dict)
      # 'First_Name=Jack&Second_Name=West#

    # Write Out Page here
    self.render("main.html", sign_query_params = sign_query_params, wall_name = cgi.escape(wall_name), user_name=user_name,
                  url = url, url_linktext = url_linktext) #removed posts_html=posts_html

class ServerPage(Handler):
  """renders server.html notes on server page"""
  def get(self):
      self.render("server.html")

class ValidationPage(Handler):
  """renders validation.html notes on html validation page"""
  def get(self):
      self.render("validation.html")

class TemplatesPage(Handler):
  """renders templates.html notes on templates page"""
  def get(self):
      self.render("templates.html")


class PostWall(webapp2.RequestHandler):
  """creates new database objects for comments"""
  def post(self):
    # We set the same parent key on the 'Post' to ensure each
    # Post is in the same entity group. Queries across the
    # single entity group will be consistent. However, the write
    # rate to a single entity group should be limited to
    # ~1/second.
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    post = Post(parent=wall_key(wall_name))

    # When the person is making the post, check to see whether the person
    # is logged into Google
    if users.get_current_user():
      post.author = Author(
            identity = users.get_current_user().user_id(),
            name = users.get_current_user().nickname(),
            email = users.get_current_user().email())
    else:
      post.author = Author(
            name = 'anonymous@anonymous.com',
            email ='anonymous@anonymous.com')


    # Get the content from our request parameters, in this case, the message
    # is in the parameter 'content'
    post.content = self.request.get('content')

# How do I verify on serverside using input verification?
    # Write to the Google Database
    post.put()

    # Do other things here such as a page redirect
    self.redirect('/?wall_name=' + wall_name)


app = webapp2.WSGIApplication([("/", MainPage),
                                ("/server", ServerPage),
                                ("/validation", ValidationPage),
                                ("/templates", TemplatesPage),
                                ('/sign', PostWall),
                                ], debug= True )
