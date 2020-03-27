from flask import Flask
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
import script

import uuid

# creates a Flask application, named app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = "static/upload/"


# a route where we will display a welcome message via an HTML template
@app.route("/")
def index():
    message = "Hello, World"
    return render_template('index.html')

@app.route("/about")
def about():
    message = "Hello, World"
    return render_template('index.html')

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
    app.run(host='0.0.0.0', port=80)