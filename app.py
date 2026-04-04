from flask import Flask, render_template_string
import datetime

app = Flask(__name__)

# --- 电子宠物类 ---
class VirtualPet:
    def __init__(self):
        self.name = "Fluffy"
        self.hunger = 50  # 饥饿值，越高越饿
        self.happiness = 50 # 快乐值，越高越开心
        self.last_interaction = datetime.datetime.now()

    def feed(self):
        self.hunger = max(0, self.hunger - 20)
        self.happiness = min(100, self.happiness + 10)
        self.last_interaction = datetime.datetime.now()
        return f"你给 {self.name} 喂了一点食物。它看起来饱了一些！"

    def play(self):
        self.happiness = min(100, self.happiness + 20)
        self.hunger = min(100, self.hunger + 10) # 玩耍会消耗能量
        self.last_interaction = datetime.datetime.now()
        return f"你和 {self.name} 玩了一会儿。它很开心！"

    def status(self):
        # 简单的“衰老”机制，每次查看状态，饥饿感会轻微增加
        time_since_interaction = (datetime.datetime.now() - self.last_interaction).seconds / 60 # 分钟
        self.hunger = min(100, self.hunger + time_since_interaction * 0.1) 
        
        status_text = f"""
        <h2>我的电子宠物: {self.name}</h2>
        <p> hunger: {self.hunger:.2f}/100 </p>
        <p> happiness: {self.happiness:.2f}/100 </p>
        <p> 最后互动时间: {self.last_interaction.strftime('%Y-%m-%d %H:%M:%S')} </p>
        <hr>
        <a href="/feed">[喂食]</a> | <a href="/play">[玩耍]</a> | <a href="/">[返回主页]</a>
        """
        
        # 根据状态改变宠物的表情
        if self.happiness < 30:
            status_text += "<p> (´;ω;｀) 它看起来不太开心...</p>"
        elif self.hunger > 70:
            status_text += "<p> (｡>﹏<｡) 它看起来很饿...</p>"
        else:
            status_text += "<p> (◕‿◕) 它看起来状态不错！</p>"
            
        return status_text

# --- 全局宠物实例 ---
# 注意：在生产环境中，用全局变量存储状态是不可靠的，因为服务器重启后会丢失。
# 但对于我们的免费实验，这是一个零成本的方案。
pet = VirtualPet()

# --- Flask 路由 ---
@app.route('/')
def home():
    html = f"""
    <h1>欢迎来到电子宠物小屋！</h1>
    <p>你的宠物正在等待你的关爱...</p>
    <a href="/pet/status">[去看看它]</a>
    """
    return html

@app.route('/pet/status')
def show_pet_status():
    return pet.status()

@app.route('/feed')
def feed_pet():
    message = pet.feed()
    # 喂食后也显示状态
    return message + "<br><br>" + pet.status()

@app.route('/play')
def play_with_pet():
    message = pet.play()
    # 玩耍后也显示状态
    return message + "<br><br>" + pet.status()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
