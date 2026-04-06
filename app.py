# app.py
import os
from flask import Flask, render_template_string, request, jsonify
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# 从环境变量中获取 GitHub Token
# 这样更安全，部署时可以通过环境变量注入
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("必须设置环境变量 GITHUB_TOKEN")

# 初始化 Azure 客户端
client = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(GITHUB_TOKEN),
)

app = Flask(__name__)

# 简单的 HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Github AI 聊天</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f0f0f0; }
        #chat-container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        #messages { height: 400px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; background-color: #fafafa; }
        .message { margin: 10px 0; padding: 8px; border-radius: 5px; }
        .user-message { background-color: #d1ecf1; text-align: right; }
        .ai-message { background-color: #f8f9fa; }
        #input-area { display: flex; }
        #user-input { flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        #send-button { padding: 10px 20px; margin-left: 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        #send-button:hover { background-color: #0056b3; }
        .typing-indicator { color: gray; font-style: italic; }
    </style>
</head>
<body>
    <div id="chat-container">
        <h2>Github AI 聊天室</h2>
        <div id="messages"></div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="输入消息..." onkeypress="handleKeyPress(event)">
            <button id="send-button" onclick="sendMessage()">发送</button>
        </div>
    </div>

    <script>
        function addMessage(sender, text) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender + '-message';
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showTypingIndicator() {
            const messagesDiv = document.getElementById('messages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typing-indicator';
            typingDiv.className = 'message ai-message typing-indicator';
            typingDiv.textContent = 'AI 正在思考...';
            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function hideTypingIndicator() {
            const typingElement = document.getElementById('typing-indicator');
            if (typingElement) {
                typingElement.remove();
            }
        }

        async function sendMessage() {
            const inputElement = document.getElementById('user-input');
            const userMessage = inputElement.value.trim();
            if (!userMessage) return;

            addMessage('user', userMessage);
            inputElement.value = '';
            
            showTypingIndicator();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: userMessage })
                });

                const data = await response.json();
                
                hideTypingIndicator();
                addMessage('ai', data.response);

            } catch (error) {
                console.error('Error:', error);
                hideTypingIndicator();
                addMessage('ai', '发生错误: ' + error.message);
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "未提供消息"}), 400

    try:
        response = client.complete(
            messages=[
                SystemMessage(content="You are a helpful assistant."),
                UserMessage(content=user_message),
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        ai_response = response.choices[0].message.content
        return jsonify({"response": ai_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 这是 Cloudfare Docker Worker 期望的入口点
# 它告诉 Gunicorn 如何加载你的应用
def main():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == '__main__':
    # 当直接运行此脚本时（本地调试），使用 Flask 内置服务器
    # 在 Docker 容器中，应由 Gunicorn 启动，此时 PORT 环境变量会被设置
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'gunicorn':
        main()
    else:
        print("请使用 Gunicorn 启动应用: gunicorn --bind 0.0.0.0:8080 app:app")
        print("或者设置环境变量 GITHUB_TOKEN 后运行: python app.py")
        app.run(debug=True, host='127.0.0.1', port=5000)
