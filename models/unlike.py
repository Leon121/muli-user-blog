from utils import *
from models.blog import Blog
from models.user import User
from google.appengine.ext import db


class Unlike(db.Model):
    post = db.ReferenceProperty(Blog, required=True)
    user = db.ReferenceProperty(User, required=True)

    @classmethod
    def by_blog_id(cls, blog_id):
        ul = Unlike.all().filter('post =', blog_id)
        return ul.count()

    @classmethod
    def check_unlike(cls, blog_id, user_id):
        cul = Unlike.all().filter('post =', blog_id).filter('user =', user_id)
        return cul.count()