import webapp2
from utils import *
from models.blog import Blog
from models.comment import Comment
from models.like import Like
from models.unlike import Unlike
from models.user import User
from google.appengine.ext import db


# Blog Handler


class BlogHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

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
        self.user = uid and User.by_id(int(uid))


# Page classes


class MainPage(BlogHandler):

    def get(self):

        blogs = db.GqlQuery(
            """SELECT * FROM
            Blog ORDER BY created
            DESC LIMIT 10""")
        if blogs:
            if self.user:
                self.render("blogs.html", blogs=blogs, username=self.user.name)
            else:
                self.render("blogs.html", blogs=blogs)


class NewPost(BlogHandler):

    def get(self):
        if self.user:
            username=self.user.name 
            self.render("newpost.html", username=username)
        else:
            self.redirect("/accessdenied")

    def post(self):  

        if not self.user:
            self.redirect("/accessdenied")
        else:
            subject = self.request.get("subject")
            content = self.request.get("content").replace('\n', '<br>')
            user_id = User.by_name(self.user.name)
            username = self.user.name

            if subject and content:
                a = Blog(
                    parent=blog_key(),
                    subject=subject,
                    content=content,
                    user=user_id)
                a.put()
                self.redirect('/post/%s' % str(a.key().id()))

            else:
                post_error = "Enter subject and content, please"
                self.render(
                    "newpost.html",
                    subject=subject,
                    content=content,
                    post_error=post_error,
                    username=username)


class PostPage(BlogHandler):

    def get(self, blog_id):
        if self.user:
            username = self.user.name 

        key = db.Key.from_path("Blog", int(blog_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.redirect("/accessdenied")


        likes = Like.by_blog_id(post)
        unlikes = Unlike.by_blog_id(post)
        post_comments = Comment.all_by_blog_id(post)
        comments_count = Comment.count_by_blog_id(post)

        if self.user:
            self.render(
                "post.html",
                post=post,
                likes=likes,
                unlikes=unlikes,
                post_comments=post_comments,
                comments_count=comments_count,
                username=username)
        else:
            self.render(
                "post.html",
                post=post,
                likes=likes,
                unlikes=unlikes,
                post_comments=post_comments,
                comments_count=comments_count)            

    def post(self, blog_id):
        key = db.Key.from_path("Blog", int(blog_id), parent=blog_key())
        post = db.get(key)
        user_id = User.by_name(self.user.name)
        comments_count = Comment.count_by_blog_id(post)
        post_comments = Comment.all_by_blog_id(post)
        likes = Like.by_blog_id(post)
        unlikes = Unlike.by_blog_id(post)
        previously_liked = Like.check_like(post, user_id)
        previously_unliked = Unlike.check_unlike(post, user_id)
        username=self.user.name

        if self.user:
            if self.request.get("like"):
                puk = post.user.key().id()
                ubn = User.by_name(self.user.name).key().id()
                if puk != ubn: # These variables were only creatd to shorten the lenght of the line of code here since it was more than 79 chars.
                    if previously_liked == 0:
                        l = Like(post=post, user=User.by_name(self.user.name))
                        l.put()
                        time.sleep(0.1)
                        self.redirect('/post/%s' % str(post.key().id()))
                    else:
                        error = "You have already liked this post"
                        self.render(
                            "post.html",
                            post=post,
                            likes=likes,
                            unlikes=unlikes,
                            error=error,
                            comments_count=comments_count,
                            post_comments=post_comments,
                            username=username)
                else:
                    error = "It's not allowed to like your own posts"
                    self.render(
                        "post.html",
                        post=post,
                        likes=likes,
                        unlikes=unlikes,
                        error=error,
                        comments_count=comments_count,
                        post_comments=post_comments,
                        username=username)

            if self.request.get("unlike"):
                puk = post.user.key().id()
                ubn = User.by_name(self.user.name).key().id()
                if puk != ubn:
                    if previously_unliked == 0:
                        ul = Unlike(
                            post=post, user=User.by_name(self.user.name))
                        ul.put()
                        time.sleep(0.1)
                        self.redirect('/post/%s' % str(post.key().id()))
                    else:
                        error = "You have already unliked this post"
                        self.render(
                            "post.html",
                            post=post,
                            likes=likes,
                            unlikes=unlikes,
                            error=error,
                            comments_count=comments_count,
                            post_comments=post_comments,
                            username=username)
                else:
                    error = "It's not allowed to unlike your own posts"
                    self.render(
                        "post.html",
                        post=post,
                        likes=likes,
                        unlikes=unlikes,
                        error=error,
                        comments_count=comments_count,
                        post_comments=post_comments,
                        username=username)

            if self.request.get("add_comment"):
                comment_text = self.request.get("comment_text")
                if comment_text:
                    c = Comment(
                        post=post,
                        user=User.by_name(self.user.name),
                        text=comment_text)
                    c.put()
                    time.sleep(0.1)
                    self.redirect('/post/%s' % str(post.key().id()))
                else:
                    comment_error = "Use the textarea to enter a post, please"
                    self.render(
                        "post.html",
                        post=post,
                        likes=likes,
                        unlikes=unlikes,
                        comments_count=comments_count,
                        post_comments=post_comments,
                        comment_error=comment_error,
                        username=username)

            if self.request.get("edit"):
                puk = post.user.key().id()
                ubn = User.by_name(self.user.name).key().id()
                if puk == ubn:
                    self.redirect('/edit/%s' % str(post.key().id()))
                else:
                    error = "To edit a post you must be the author"
                    self.render(
                        "post.html",
                        post=post,
                        likes=likes,
                        unlikes=unlikes,
                        comments_count=comments_count,
                        post_comments=post_comments,
                        error=error,
                        username=username)

            if self.request.get("delete"):
                puk = post.user.key().id()
                ubn = User.by_name(self.user.name).key().id()
                if puk == ubn:
                    db.delete(key)
                    time.sleep(0.1)
                    self.redirect('/')
                else:
                    error = "To delete a post you must be the author"
                    self.render(
                        "post.html",
                        post=post,
                        likes=likes,
                        unlikes=unlikes,
                        comments_count=comments_count,
                        post_comments=post_comments,
                        error=error,
                        username=username)
        else:
            self.redirect("/login")


class DeleteComment(BlogHandler):

    def get(self, post_id, comment_id):
        comment = Comment.get_by_id(int(comment_id))

        if comment and self.user:
            if comment.user.name == self.user.name:
                db.delete(comment)
                time.sleep(0.1)
                self.redirect('/post/%s' % str(post_id))
            else:
                self.write("To delete a comment you must be the author")
        else:
            self.write("This comment no longer exists")


class EditComment(BlogHandler):

    def get(self, post_id, comment_id):
        post = Blog.get_by_id(int(post_id), parent=blog_key())
        comment = Comment.get_by_id(int(comment_id))
        username = self.user.name

        if comment and self.user:
            if comment.user.name == self.user.name:
                self.render(
                    "editcomment.html",
                    comment_text=comment.text,
                    username=username)
            else:
                error = "To edit a comment you must be the author'"
                self.render(
                    "editcomment.html",
                    edit_error=error,
                    username=username)
        else:
            error = "This comment no longer exists"
            self.render(
                "editcomment.html",
                edit_error=error,
                username=username)

    def post(self, post_id, comment_id):
        if self.request.get("update_comment"):
            comment = Comment.get_by_id(int(comment_id))
            username = self.user.name

            if comment.user.name == self.user.name:
                comment.text = self.request.get('comment_text')
                comment.put()
                time.sleep(0.1)
                self.redirect('/post/%s' % str(post_id))
            else:
                error = "To edit a comment you must be the author'"
                self.render(
                    "editcomment.html",
                    comment_text=comment.text,
                    edit_error=error,
                    username=username)
        elif self.request.get("cancel"):
            self.redirect('/post/%s' % str(post_id))


class EditPost(BlogHandler):

    def get(self, blog_id):

        key = db.Key.from_path("Blog", int(blog_id), parent=blog_key())
        post = db.get(key)

        if self.user:
            username=self.user.name
            puk = post.user.key().id()
            ubn = User.by_name(self.user.name).key().id()
            if puk == ubn:
                self.render(
                "editpost.html",
                post=post,
                username=username)
            else:
                self.response.out.write(
                    "'''To edit a post you must be the author""")
        else:
            self.redirect("/login")

    def post(self, blog_id):

        if self.user:

            key = db.Key.from_path("Blog", int(blog_id), parent=blog_key())
            post = db.get(key)
            username = self.user.name

        if self.request.get("update"):
            subject = self.request.get("subject")
            content = self.request.get("content").replace('\n', '<br>')
            puk = post.user.key().id()
            ubn = User.by_name(self.user.name).key().id()
            if puk == ubn:
                if subject and content:
                    post.subject = subject
                    post.content = content
                    post.put()
                    time.sleep(0.1)
                    self.redirect('/post/%s' % str(post.key().id()))
                else:
                    post_error = "Enter a subject and content, please"
                    self.render(
                        "editpost.html",
                        subject=subject,
                        content=content,
                        post_error=post_error,
                        username=username)
            else:
                self.response.out.write(
                    """To edit a post you must be the author""")
        elif self.request.get("cancel"):
            self.redirect('/post/%s' % str(post.key().id()))


class Signup(BlogHandler):

    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username=self.username, email=self.email)

        if not valid_username(self.username):
            params['error_username'] = "Not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "Not a valid password."
            have_error = True

        if not self.password == self.verify:
            params['error_verify'] = "Passwords didn't match"
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "Please enter a valid email"
            have_error = True

        if have_error:
            self.render("signup.html", **params)

        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(Signup):

    def done(self):
        u = User.by_name(self.username)

        if u:
            error = 'That user already exists.'
            self.render('signup.html', error_username=error)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/welcome')


class Welcome(BlogHandler):

    def get(self):
        blogs = db.GqlQuery(
            """SELECT * FROM Blog
            ORDER BY created
            DESC LIMIT 10""")
        if self.user:
            self.render(
                "welcome.html",
                username=self.user.name,
                blogs=blogs)
        else:
            self.redirect("/login")


class AccessDenied(BlogHandler):

    def get(self):
        self.render('accessdenied.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)

        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            error = 'Invalid login'
            self.render('login.html', error=error)


class Login(BlogHandler):

    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)

        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            error = 'Invalid login'
            self.render('login.html', error=error)


class Logout(BlogHandler):

    def get(self):

        if self.user:
            self.logout()
            self.redirect("/login")


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newpost', NewPost),
    ('/post/([0-9]+)', PostPage),
    ('/accessdenied', AccessDenied),
    ('/login', Login),
    ('/logout', Logout),
    ('/signup', Register),
    ('/welcome', Welcome),
    ('/edit/([0-9]+)', EditPost),
    ('/blog/([0-9]+)/editcomment/([0-9]+)', EditComment),
    ('/blog/([0-9]+)/deletecomment/([0-9]+)', DeleteComment),
    ], debug=True)
