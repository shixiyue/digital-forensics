from github_webhook import Webhook
from flask import Flask, jsonify
import subprocess

app = Flask(__name__)  # Standard Flask app
webhook = Webhook(app)  # Defines '/postreceive' endpoint


@webhook.hook()        # Defines a handler for the 'push' event
def on_push(data):
    if data['commits'][0]['distinct'] == True:
        try:
            cmd_output = subprocess.check_output(
                ['git', 'pull', 'origin', 'master'],)
            return jsonify({'msg': str(cmd_output)})
        except subprocess.CalledProcessError as error:
            return jsonify({'msg': str(error.output)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8100)
