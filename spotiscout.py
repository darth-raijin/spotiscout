from flask import Flask, request, render_template, Response
from tracks import tracks
from albums import albums
from genres import genres
from recent import recent


app = Flask(__name__)

# Registering blueprints
app.register_blueprint(tracks)
app.register_blueprint(albums)
app.register_blueprint(genres)
app.register_blueprint(recent)


@app.route("/")
def method():
    return NotImplemented


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)