from flask import Flask, Response
from PIL import Image, ImageDraw, ImageFont
import io
import datetime

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <h1>🎉 恭喜你！你的 Python 应用已经在 Claw Cloud 上运行了！</h1>
    <p>点击下面的链接，动态生成一张带有时戳的图片：</p>
    <a href="/generate-image" target="_blank">生成图片</a>
    """

@app.route('/generate-image')
def generate_image():
    """动态生成一张包含当前时间的图片"""
    
    # 1. 创建一张空白图片 (宽度, 高度, 背景色)
    img_width, img_height = 400, 200
    img = Image.new('RGB', (img_width, img_height), color = (73, 109, 137))
    
    # 2. 创建一个绘图对象
    d = ImageDraw.Draw(img)

    # 3. 准备文字内容
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"当前时间戳:\n{current_time_str}"

    # 4. (可选) 加载字体, 如果不加载，会使用默认字体
    # font = ImageFont.truetype("arial.ttf", size=20) # Windows
    # font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=20) # Linux
    
    # 5. 在图片上绘制文字
    # d.text((x坐标, y坐标), 文字, fill=(R, G, B颜色))
    d.text((50, 50), text, fill=(255, 255, 0)) # 黄色文字

    # 6. 将图片保存到内存中的一个字节流
    img_io = io.BytesIO()
    img.save(img_io, 'PNG') # 保存为 PNG 格式
    img_io.seek(0) # 将指针移到开头

    # 7. 将内存中的图片作为 HTTP 响应返回
    # Response(数据, mimetype=媒体类型)
    return Response(img_io.getvalue(), mimetype='image/png')

# 这部分在使用 Gunicorn 时会被忽略，因为我们用 CMD ["gunicorn", ...] 启动
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
