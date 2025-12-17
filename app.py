from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "SD PBL APP"

if __name__ == "__main__":
    app.run()
