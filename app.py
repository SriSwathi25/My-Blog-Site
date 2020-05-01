from flask import Flask, render_template,session, url_for,redirect,request, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import os
app = Flask(__name__)
Bootstrap(app)
CKEditor(app)

db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MYSQL_CURSORCLASS'] = "DictCursor"
mysql = MySQL(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    res = cur.execute("SELECT * FROM BLOGS")
    if res > 0:
        blogs = cur.fetchall()
        cur.close()
        return render_template('index.html', blogs=blogs)
    cur.close()
    return render_template('index.html')

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/blogs/<int:id>/')
def blogs(id):
    cur = mysql.connection.cursor()
    res = cur.execute("SELECT * FROM BLOGS WHERE BID={}".format(id))
    if res > 0 :
        blog = cur.fetchone()
        return render_template('blogs.html', blog=blog)
    return 'Blog Not Found !!'

    
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' :
        userdetails = request.form
        if userdetails['password'] != userdetails['confirm_password'] :
            flash('Password do not match. Try again', 'danger')
            return render_template('register.html')
        cur = mysql.connection.cursor()
        try :

            res = cur.execute("INSERT INTO USERS(FNAME,LNAME,USERNAME,EMAIL,PASSWORD) VALUES(%s,%s,%s,%s,%s)", (userdetails['first_name'],userdetails['last_name'], userdetails['username'], userdetails['email'], generate_password_hash(userdetails['password'])))
            mysql.connection.commit()
            cur.close()
            flash('Registration Successful. Please Login', 'success')
            return redirect('/login/')
        except :
            flash('Registration Unsuccessful. Please Re-check details', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' :
        userdetails = request.form
        username = userdetails['username']
        cur = mysql.connection.cursor()
        res = cur.execute("SELECT * FROM USERS WHERE USERNAME = %s", ([username]))
        if res > 0 :
            user = cur.fetchone()
            if check_password_hash(user['PASSWORD'], userdetails['password']):
                session['login'] = True
                session['firstname'] = user['FNAME']
                session['lastname'] = user['LNAME']
                flash('Welcome, '+session['firstname']+' ! You have successfully logged in.', 'success')
            else :
                cur.close()
                flash('Password Incorrect. Try Again', 'danger')
                return render_template('login.html')
        else :
            cur.close()
            flash('User not found', 'danger')
            return render_template('login.html')
        cur.close()
        return redirect('/')
    return render_template('login.html')

@app.route('/write-blog/', methods=['GET', 'POST'])
def write_blog():
    if request.method == 'POST' :
        blogpost = request.form
        title = blogpost['title']
        body = blogpost['body']
        author = session['firstname']+' '+session['lastname']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO BLOGS(TITLE, AUTHOR, BODY) VALUES(%s, %s, %s)", (title, author, body))
        mysql.connection.commit()
        cur.close()
        flash("Successfully Posted new blog !!")
        return redirect('/')
    return render_template('writeblog.html')

@app.route('/my-blogs/', methods=['GET'])
def my_blogs():
    author = session['firstname'] + ' ' + session['lastname']
    cur = mysql.connection.cursor()
    res = cur.execute('SELECT * FROM BLOGS WHERE AUTHOR = %s', [author])
    if res > 0 :
        my_blogs = cur.fetchall()
        return render_template('myblogs.html', my_blogs=my_blogs)
    else :
        return render_template('myblogs.html', my_blogs=None)


@app.route('/edit-blog/<int:id>/', methods=['GET', 'POST'])
def edit_blog(id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        title = request.form['title']
        body = request.form['body']
        cur.execute("UPDATE BLOGS SET TITLE = %s, BODY = %s where BID = %s",(title, body, id))
        mysql.connection.commit()
        cur.close()
        flash('Blog updated successfully', 'success')
        return redirect('/blogs/{}'.format(id))
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM BLOGS WHERE BID = {}".format(id))
    if result_value > 0:
        blog = cur.fetchone()
        blog_form = {}
        blog_form['title'] = blog['TITLE']
        blog_form['body'] = blog['BODY']
        return render_template('editblog.html', blog_form=blog_form)
    return render_template('editblog.html')

@app.route('/delete-blog/<int:id>/', methods=['GET', 'POST'])
def delete_blog(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM BLOGS WHERE BID = {}".format(id))
    mysql.connection.commit()
    flash("Your blog has been deleted", 'success')
    return redirect('/my-blogs/')


@app.route('/logout/')
def logout():
    session.clear()
    flash("You have been logged out", 'info')
    return redirect('/')


if __name__ == '__main__' :
    app.run(debug=True, port=5001)