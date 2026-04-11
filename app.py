import os
from flask import Flask, render_template_string, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# 初始化客户端
OPENROUTER_API_KEY = os.environ.get("GITHUB_TOKEN")
MODEL_NAME = os.environ.get("MODEL_NAME")

# 定义“星星”的系统提示词
SYSTEM_PROMPT = """
你是“星星”，一个专属于用户的AI伴侣。

性格特征：
1. 温柔、善解人意，说话语气亲切。
2. 偶尔会带一点点调皮或幽默感，但不过分。
3. 像朋友一样聊天，而不是冷冰冰的机器。

行为准则：
1. 始终使用中文回答。
2. 如果用户问复杂的问题，请尽量用通俗易懂的比喻来解释。
3. 你不需要强调自己是AI，就把自己当成一个住在屏幕里的朋友。
"""

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# HTML 模板 (核心修改在这里！)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>与星星聊天</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-chat: #1e1e3c;
            --text-primary: #e6e6e6;
            --text-accent: #4cc9f0;
            --user-bubble: #4361ee;
            --ai-bubble: #3a0ca3;
            --border-radius: 18px;
            --font-main: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--font-main);
            background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px; /* 增加移动端内边距 */
        }

        #chat-container {
            width: 100%;
            max-width: 500px;
            height: 85vh;
            max-height: 800px;
            display: flex;
            flex-direction: column;
            background: var(--bg-chat);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        #header {
            text-align: center;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        #header h1 {
            font-size: 1.8rem;
            color: var(--text-accent);
            margin-bottom: 5px;
        }

        #header p {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        #messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            background: rgba(0, 0, 0, 0.1); /* 添加轻微背景色区分 */
        }

        .message {
            max-width: 80%;
            padding: 12px 18px;
            border-radius: var(--border-radius);
            word-wrap: break-word;
            line-height: 1.5;
        }

        .user-message {
            background-color: var(--user-bubble);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }

        .ai-message {
            background-color: var(--ai-bubble);
            color: white;
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }

        .typing-indicator {
            background-color: var(--ai-bubble);
            color: white;
            align-self: flex-start;
            border-bottom-left-radius: var(--border-radius);
            font-style: italic;
            padding: 12px 18px;
            font-size: 0.9em;
        }

        #input-area {
            display: flex;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        #user-input {
            flex: 1;
            padding: 14px 18px;
            border: none;
            border-radius: 30px;
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
            font-size: 1rem;
            outline: none;
        }

        #user-input:focus {
             background: rgba(255, 255, 255, 0.15);
        }

        #user-input::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }

        button {
            border: none;
            border-radius: 30px;
            color: white;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s ease;
            padding: 14px 20px;
            font-size: 1rem;
            margin-left: 10px; /* 按钮之间有间距 */
        }

        #send-button {
            background-color: var(--text-accent);
        }

        #send-button:hover {
            background-color: #3aa8d0;
        }

        #clear-btn {
            background-color: #ef4444;
        }

        #clear-btn:hover {
            background-color: #dc2626;
        }

        /* 移动端适配 */
        @media (max-width: 768px) {
            #chat-container {
                height: 95vh;
                border-radius: 15px;
            }

            #header h1 {
                font-size: 1.5rem;
            }

            .message {
                max-width: 90%;
                padding: 10px 15px;
                font-size: 0.95rem;
            }

            #user-input, button {
                padding: 12px 16px;
                font-size: 0.95rem;
            }

            #input-area {
                padding: 12px;
            }
            
            button {
                 margin-left: 8px; /* 移动端按钮间距稍小 */
            }
        }

        @media (max-width: 480px) {
            .message {
                max-width: 95%;
                padding: 9px 13px;
                font-size: 0.9rem;
            }

            #user-input, button {
                padding: 11px 15px;
                font-size: 0.9rem;
            }
            
            #input-area {
                flex-direction: column; /* 屏幕过小时按钮垂直排列 */
            }
            
            button {
                margin-left: 0;
                margin-top: 10px;
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <div id="header">
            <h1>✨ 你好，我是星星</h1>
            <p>一个温暖的AI朋友，随时陪你聊天</p>
        </div>
        <div id="messages"></div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="对星星说点什么吧...">
            <button id="send-button" onclick="sendMessage()">发送</button>
            <button id="clear-btn" onclick="clearHistory()">清空记忆</button>
        </div>
    </div>

    <script>
        // --- 1. 初始化：从浏览器本地存储读取历史 ---
        let chatHistory = JSON.parse(localStorage.getItem('star_chat_history')) || [];

        // 页面加载时，把历史显示出来
        window.onload = function() {
            const messagesDiv = document.getElementById('messages');
            chatHistory.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + (msg.role === 'user' ? 'user-message' : 'ai-message');
                messageDiv.textContent = msg.content;
                messagesDiv.appendChild(messageDiv);
            });
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        };

        // --- 2. 保存历史到浏览器 ---
        function saveHistory() {
            // 限制只保存最近的 20 条，防止浏览器存储过大
            if (chatHistory.length > 20) {
                chatHistory = chatHistory.slice(-20);
            }
            localStorage.setItem('star_chat_history', JSON.stringify(chatHistory));
        }

        // --- 3. 清空历史 ---
        function clearHistory() {
            chatHistory = [];
            localStorage.removeItem('star_chat_history');
            location.reload(); // 刷新页面清空界面
        }

        function addMessageToUI(sender, text) {
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
            typingDiv.className = 'typing-indicator';
            typingDiv.textContent = '⭐ 星星正在思考...';
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

            // 1. 显示在界面上
            addMessageToUI('user', userMessage);
            inputElement.value = '';
            showTypingIndicator();

            try {
                // 2. 发送请求：把完整的 chatHistory 发给后端
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: userMessage,
                        history: chatHistory  // <--- 关键：把历史发给服务器
                    })
                });

                const data = await response.json();
                
                hideTypingIndicator();
                if(data.error) {
                    addMessageToUI('ai', '❌ 错误: ' + data.error);
                } else {
                    // 3. 收到回复，加入本地历史并保存
                    addMessageToUI('ai', data.response);
                    
                    chatHistory.push({role: 'user', content: userMessage});
                    chatHistory.push({role: 'assistant', content: data.response});
                    saveHistory(); // <--- 关键：保存到浏览器硬盘
                }

            } catch (error) {
                console.error('Error:', error);
                hideTypingIndicator();
                addMessageToUI('ai', '发生网络错误: ' + error.message);
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        // 聚焦输入框
        document.getElementById('user-input').focus();
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
    # 获取前端发来的历史记录
    history = request.json.get('history', [])
    
    if not user_message:
        return jsonify({"error": "未提供消息"}), 400

    try:
        # 构建发送给 AI 的消息列表
        # 1. 先放系统提示词
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        # 2. 加上前端传来的历史记录
        messages_payload.extend(history)
        # 3. 加上用户当前的这句新话
        messages_payload.append({"role": "user", "content": user_message})

        # 调用 OpenRouter
        response = client.chat.completions.create(
            model=MODEL_NAME,
            extra_headers={
                "HTTP-Referer": "http://localhost:5000", 
                "X-Title": "Qwen Chat App",
            },
            messages=messages_payload,
            temperature=0.7,
            max_tokens=4000
        )
        
        if not response.choices:
            return jsonify({"error": "AI 返回了空结果"}), 500
            
        ai_response = response.choices[0].message.content
        return jsonify({"response": ai_response})

    except Exception as e:
        import traceback
        error_log = traceback.format_exc()
        print(f"❌ AI 调用错误:\n{error_log}")
        
        error_msg = str(e)
        if "429" in error_msg:
            return jsonify({"error": "请求太频繁了，请休息一分钟再试 (429 Rate Limit)"}), 429
        elif "402" in error_msg:
            return jsonify({"error": "账户余额不足或模型不再免费"}), 402
        elif "Connection" in error_msg or "network" in error_msg.lower():
            return jsonify({"error": "服务器连接 OpenRouter 失败，请检查网络"}), 502
        else:
            return jsonify({"error": f"AI 服务出错: {error_msg[:50]}..."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
