from flask import render_template , url_for , flash , redirect ,flash ,request
from csgonews import app , bcrypt
from csgonews.modules import *
import os
import secrets
from PIL import Image
from csgonews.form import RegistrationForm,LoginForm,UpdateAccountForm,NewPostForm,UpdatePostForm,CommentForm
from flask_login import login_user ,current_user ,logout_user,login_required

@app.route('/',methods=['POST','GET'])
@app.route('/home',methods=['POST','GET'])
def home():
    posts = Post.query.order_by(Post.date_posted).all()
    tags =  Tag.query.order_by(Tag.id).all()
    return render_template('home.html', title='home',tags=tags,posts=posts)

@app.route('/login',methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            flash(f"Succesfully logged in {form.email.data}","success")
            login_user(user,remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f"email or password is wrong please check","danger")
    return render_template('login.html', title='LogIn',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register',methods=['POST','GET'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,email=form.email.data,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f"Your account has been created {form.username.data}","success")
        return redirect(url_for('login'))
        
    return render_template('register.html', title='Register', form=form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

#managing profiles
@app.route('/profile' , methods = ['POST','GET'])
@login_required
def profile():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            file_name=current_user.image
            current_user.image= picture_file
            remove_file(file_name)
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image = url_for('static', filename='profile/' + current_user.image)
    return render_template('profile.html',title = 'profile',image_file=image,form=form)

#steal recent news from valve
@app.route('/valvenews')
def valvenews():
    return render_template('valvenews.html',title='valvenews')

#brag about my self
@app.route('/aboutme')
def aboutme():
    return render_template('aboutme.html',title='aboutme')

# remove un used items
def remove_file(filename):
    os.remove(os.path.join(app.root_path,'static/profile', filename))

@app.route('/post/new',methods=['POST','GET'])
@login_required
def newpost():
    form = NewPostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been posted!', 'success')
        return redirect(url_for('home'))
    return render_template('newpost.html',title='NewPost',form = form)

@app.route('/post/<psid>',methods=['POST','GET'])
def post(psid):
    form = CommentForm()
    post = Post.query.get_or_404(psid)
    if form.validate_on_submit():
        comment = Comment(comment=form.comment.data,post_id=post.id,user_id=current_user.id)
        db.session.add(comment)
        db.session.commit()
    return render_template('viewpost.html',title=f'post{psid}' ,post=post,form= form)

@app.route('/post/<psid>/update',methods=['POST','GET'])
@login_required
def updatepost(psid):
    post = Post.query.get_or_404(psid)
    form = UpdatePostForm()
    if current_user.id != post.author.id :
        flash('Your not the author of this post', 'danger')
        return redirect(url_for(f'home')) 
    else :
        if form.validate_on_submit():
            post.title = form.title.data 
            post.content = form.content.data
            db.session.commit()
            flash('Post edited successfully', 'success')
            return redirect(url_for("post",psid=post.id))
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        return render_template('updatepost.html',title='UpdatePost',form = form)

@app.route('/post/<psid>/delete',methods=['POST','GET'])
@login_required
def deletepost(psid):
    post = Post.query.get_or_404(psid)
    if post.author.id != current_user.id:
        flash('Your not the author of this post', 'danger')
        return redirect(url_for('home'))
    else:
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('home'))