from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "🎉 恭喜你！你的 Python 应用已经在 Claw Cloud 上运行了！"

