from flask import Flask, render_template, request, redirect, flash
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re
from werkzeug.utils import secure_filename
from models import db, Post, MyUser,Like


app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(24)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return MyUser.select().where(MyUser.id==int(user_id)).first()


@app.before_request
def before_request():
    db.connect()
    
@app.after_request
def after_request(response):
    db.close()
    return response


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        user = MyUser.select().where(MyUser.email==email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect('/login/')
        else:
            login_user(user)
            return redirect('/')
    return render_template('login.html')

@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/login/')

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    return True

def save_avatar(file):
    if not file:
        return None
    filename = secure_filename(file.filename)
    file.save(os.path.join(cover_folder, filename))
    return filename

@app.route('/register/', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        age = request.form['age']
        full_name = request.form['full_name']
        password = request.form['password']
        avatar = request.files['avatar']  
        user = MyUser.select().where(MyUser.email == email).first()
        if user:
            flash('email address already exists')
            return redirect('/register/')
        if MyUser.select().where(MyUser.username == username).first():
            flash('username already exists')
            return redirect('/register/')
        else:
            if validate_password(password):
                avatar_filename = save_avatar(avatar)
                MyUser.create(
                    email=email,
                    username=username,
                    age=age,
                    password=generate_password_hash(password),
                    full_name=full_name,
                    avatar_filename=avatar_filename
                )
                return redirect('/login/')
            else:
                flash('wrong password')
                return redirect('/register/')
    return render_template('register.html')



cover_folder = os.path.join('static', 'media')

@app.route('/create/', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        cover_file = request.files['cover']
        if cover_file.filename != '':
            filename = secure_filename(cover_file.filename)
            cover_file.save(os.path.join(cover_folder, filename))
        else:
            filename = None

        Post.create(
            title=title,
            author=current_user,
            content=content,
            cover_filename=filename
        )
        return redirect('/')
    return render_template('create.html')

    
@app.route('/<int:id>/')
def get_post(id):
    post = Post.select().where(Post.id==id).first()
    if post:
        return render_template('post_detail.html', post=post)
    return f'Post with id = {id} does not exists'

@app.route('/current_profile/')
@login_required
def current_profile():
    print("Current User ID:", current_user.id) 
    user_posts = Post.select().where(Post.author == current_user)
    return render_template('profile.html', user=current_user, user_posts=user_posts)

@app.route('/profile/<int:user_id>/')
def profile(user_id):
    user = MyUser.get_or_none(MyUser.id == user_id)
    if user:
        user_posts = Post.select().where(Post.author == user)
        return render_template('profile.html', user=user, user_posts=user_posts)
    else:
        flash('User not found.')
        return redirect('/login/')



    
avatar_folder = os.path.join('static', 'media')

@app.route('/update_profile/', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        email = request.form['email']
        full_name = request.form['full_name']
        age = request.form['age']


        current_user.email = email
        current_user.full_name = full_name
        current_user.age = age

    
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar.filename != '':
                filename = secure_filename(avatar.filename)

                if not os.path.exists(avatar_folder):
                    os.makedirs(avatar_folder)
                avatar.save(os.path.join(avatar_folder, filename)) 
                current_user.avatar_filename = filename 

        current_user.save()

        print("User ID:", current_user.id)
        print("User Email:", current_user.email)
        print("User Full Name:", current_user.full_name)
        print("User Age:", current_user.age)
        print("Avatar Filename:", current_user.avatar_filename)

        flash('Profile updated successfully.')
        return redirect('/current_profile/')

    return redirect('/current_profile/')


@app.route('/<int:id>/update/', methods=['GET', 'POST'])
@login_required
def update(id):
    post = Post.select().where(Post.id==id).first()
    if request.method == 'POST':
        if post:
            if current_user == post.author:
                title = request.form["title"]
                content = request.form["content"]
                cover_file = request.files['cover']

                if cover_file.filename != '':
                    filename = secure_filename(cover_file.filename)
                    cover_file.save(os.path.join(cover_folder, filename))
                else:
                    filename = post.cover_filename

                obj = Post.update({
                    Post.title: title,
                    Post.content: content,
                    Post.cover_filename: filename 
                }).where(Post.id == id)
                obj.execute()
                return redirect(f'/{id}/')
            return f'you are not author of this post'
        return f'Post with id = {id} does not exists'
    return render_template('update.html', post=post)


@app.route('/<int:id>/delete/', methods=('GET', 'POST'))
@login_required
def delete(id):
    post = Post.select().where(Post.id==id).first()
    if request.method == 'POST':
        if post:
            if current_user==post.author:
                post.delete_instance()
                return redirect('/')
            return f'you are not author of this post'
        return f'Post with id = {id} does not exist'
    return render_template('delete.html', post=post)

@app.route('/like/<int:post_id>/', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.get_or_none(Post.id == post_id)
    if post:
        like = Like.get_or_none(Like.user == current_user, Like.post == post)
        if not like:
            Like.create(user=current_user, post=post)
    return redirect('/')  # Перенаправление на главную страницу


@app.route('/unlike/<int:post_id>/', methods=['POST'])
@login_required
def unlike_post(post_id):
    post = Post.get_or_none(Post.id == post_id)
    if post:
        like = Like.get_or_none(Like.user == current_user, Like.post == post)
        if like:
            like.delete_instance()
    return redirect('/') 



@app.route('/')
def index():
    all_posts = Post.select()
    likes = Like.select() 
    return render_template('index.html', posts=all_posts, likes=likes, Like=Like)

if __name__ == '__main__':
    app.run(debug=True)
