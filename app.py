from flask import Flask
from flask import Flask, flash, request, redirect, url_for, make_response, render_template, jsonify
from werkzeug.utils import secure_filename
import os
import subprocess
import script
from forms import LoginForm, SignupForm

from github_webhook import Webhook

import uuid

# creates a Flask application, named app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = "static/upload/"
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

webhook = Webhook(app) # Defines '/postreceive' endpoint

# a route where we will display a welcome message via an HTML template
@app.route("/404")
def page404():
    return render_template('404.html')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')

@app.route("/about")
def about():
    return render_template('index.html')

@app.route("/abc")
def certificate():
    return render_template('certificate.html')

@app.route('/logout', methods = ['GET'])
def logout():
    resp = make_response(redirect(url_for('index')))
    resp.delete_cookie('df_user')
    return resp

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
      resp = make_response(redirect(url_for('dashboard')))
      resp.set_cookie('df_user', form.email.data)
      return resp
    return render_template('login.html', form=form)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
      flash('Verification email sent to {}'.format(form.email.data))
      resp = make_response(redirect(url_for('dashboard')))
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
            return render_template('dashboard.html', filename=result)

    return render_template('dashboard.html')

@webhook.hook()        # Defines a handler for the 'push' event
def on_push(data):
    if data['commits'][0]['distinct'] == True:
        try:
            cmd_output = subprocess.check_output(['git', 'pull', 'origin', 'master'],)
            return jsonify({'msg': str(cmd_output)})
        except subprocess.CalledProcessError as error:
            return jsonify({'msg': str(error.output)})

# run the application
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)
