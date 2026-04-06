import os
from flask import Flask, render_template_string, request, jsonify
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

app = Flask(__name__)

# 1. 获取 Token
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# 2. 初始化客户端 (放在全局，避免每次请求都重新连接)
client = None
if GITHUB_TOKEN:
    try:
        client = ChatCompletionsClient(
            endpoint="https://models.github.ai/inference",
            credential=AzureKeyCredential(GITHUB_TOKEN),
        )
        print("✅ Azure AI 客户端初始化成功")
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
else:
    print("⚠️ 警告: 未找到 GITHUB_TOKEN 环境变量，AI 功能将无法使用")

# HTML 模板保持不变
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
                if(data.error) {
                    addMessage('ai', '❌ 错误: ' + data.error);
                } else {
                    addMessage('ai', data.response);
                }

            } catch (error) {
                console.error('Error:', error);
                hideTypingIndicator();
                addMessage('ai', '发生网络错误: ' + error.message);
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
    if not client:
        return "服务器错误：未配置 GITHUB_TOKEN，请检查环境变量。", 500
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    # 1. 检查客户端是否初始化
    if not client:
        return jsonify({"error": "服务器未配置 Token"}), 500

    # 2. 获取用户消息
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "未提供消息"}), 400

    try:
        # 3. 调用 AI (增加了 model 参数)
        response = client.complete(
            messages=[
                SystemMessage(content="You are a helpful assistant."),
                UserMessage(content=user_message),
            ],
            model="deepseek/DeepSeek-V3-0324", # 显式指定模型
            temperature=0.7,
            max_tokens=1000,
        )
        ai_response = response.choices[0].message.content
        return jsonify({"response": ai_response})

    except Exception as e:
        # 打印详细错误到服务器日志
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# 移除复杂的 __main__ 逻辑，完全交给 Gunicorn 处理
