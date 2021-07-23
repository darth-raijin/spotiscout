from flask import Flask, request, render_template, Response

app = Flask(__name__)


database = Database()
fake = Faker()


@app.route("/")
def method():
    return NotImplemented


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)