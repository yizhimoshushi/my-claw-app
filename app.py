from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "🎉 恭喜你！你的 Python 应用已经在 Claw Cloud 上运行了！"

# 关键点：host='0.0.0.0' 允许外部访问
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
