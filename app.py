import os
from flask import Flask, render_template_string, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# 1. 初始化 OpenRouter 客户端
# 注意：这里直接使用了你提供的 Key，实际部署时建议放在环境变量里更安全
OPENROUTER_API_KEY = os.environ.get("GITHUB_TOKEN")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# HTML 模板 (保持原样，界面不变)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Qwen3.6 Plus 聊天</title>
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
        <h2>Qwen3.6 Plus 聊天室 (1M Context)</h2>
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
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "未提供消息"}), 400

    try:
        # 调用 OpenRouter (Qwen3.6 Plus)
        response = client.chat.completions.create(
            model="qwen/qwen3.6-plus:free", # 使用你指定的模型
            extra_headers={
                "HTTP-Referer": "http://localhost:5000", 
                "X-Title": "Qwen Chat App",
            },
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=4000 # 稍微调大一点，因为它是免费且强大的模型
        )
        
        # 检查返回结果
        if not response.choices:
            return jsonify({"error": "AI 返回了空结果"}), 500
            
        ai_response = response.choices[0].message.content
        return jsonify({"response": ai_response})

    except Exception as e:
        import traceback
        error_log = traceback.format_exc()
        print(f"❌ AI 调用错误:\n{error_log}")
        
        error_msg = str(e)
        # 针对 OpenRouter 的常见错误处理
        if "429" in error_msg:
            return jsonify({"error": "请求太频繁了，请休息一分钟再试 (429 Rate Limit)"}), 429
        elif "402" in error_msg:
            return jsonify({"error": "账户余额不足或模型不再免费"}), 402
        elif "Connection" in error_msg or "network" in error_msg.lower():
            return jsonify({"error": "服务器连接 OpenRouter 失败，请检查网络"}), 502
        else:
            return jsonify({"error": f"AI 服务出错: {error_msg[:50]}..."}), 500
