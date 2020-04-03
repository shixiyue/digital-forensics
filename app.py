from flask import Flask
from flask import Flask, flash, request, redirect, url_for, make_response, render_template
from werkzeug.utils import secure_filename
import os
import script
from forms import LoginForm, SignupForm

import uuid

# creates a Flask application, named app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = "static/upload/"
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

# a route where we will display a welcome message via an HTML template
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('index.html')

@app.route('/logout', methods = ['GET'])
def logout():
    resp = make_response(redirect(url_for('index')))
    resp.delete_cookie('df_user')
    return resp

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
      flash('Login requested for user {}, remember_me={}'.format(
        form.email.data, form.remember_me.data))
      resp = make_response(redirect(url_for('index')))
      resp.set_cookie('df_user', form.email.data)
      return resp
    return render_template('login.html', form=form)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
      flash('Verification email sent to {}'.format(form.email.data))
      resp = make_response(redirect(url_for('index')))
      return resp
    return render_template('signup.html', form=form)

@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            uid = str(uuid.uuid4())
            image_dir = os.path.join(app.config['UPLOAD_FOLDER'], uid)
            os.mkdir(image_dir)
            file.save(os.path.join(image_dir, filename))
            script.check_images(image_dir)
            basename, ext = os.path.splitext(filename)
            result = os.path.join(image_dir, "ela_results", basename + ".ela.png")
            return render_template('index.html', filename=result)

    return render_template('index.html')

# run the application
if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=80)