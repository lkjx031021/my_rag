// 全局变量
let chatHistory = [];
let currentChatId = null;
let isStreaming = false;

// DOM 元素
const elements = {
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    chatMessages: document.getElementById('chatMessages'),
    loadingIndicator: document.getElementById('loadingIndicator'),
    sidebar: document.getElementById('sidebar'),
    menuBtn: document.getElementById('menuBtn'),
    newChatBtn: document.getElementById('newChatBtn'),
    chatHistory: document.getElementById('chatHistory'),
    settingsBtn: document.getElementById('settingsBtn'),
    settingsModal: document.getElementById('settingsModal'),
    settingsModalClose: document.getElementById('settingsModalClose'),
    uploadBtn: document.getElementById('uploadBtn'),
    fileInput: document.getElementById('fileInput'),
    charCount: document.getElementById('charCount'),
    systemPrompt: document.getElementById('systemPrompt'),
    streamingToggle: document.getElementById('streamingToggle')
};

// 初始化应用
function initApp() {
    setupEventListeners();
    setupAutoResize();
    loadChatHistory();
    updateCharCount();
}

// 设置事件监听器
function setupEventListeners() {
    // 发送消息
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.messageInput.addEventListener('keydown', handleKeyDown);
    elements.messageInput.addEventListener('input', updateCharCount);

    // 侧边栏控制
    elements.menuBtn.addEventListener('click', toggleSidebar);
    elements.newChatBtn.addEventListener('click', startNewChat);

    // 设置模态框
    elements.settingsBtn.addEventListener('click', showSettingsModal);
    elements.settingsModalClose.addEventListener('click', hideSettingsModal);
    elements.settingsModal.addEventListener('click', (e) => {
        if (e.target === elements.settingsModal) {
            hideSettingsModal();
        }
    });

    // 文件上传
    elements.uploadBtn.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileUpload);

    // 键盘快捷键
    document.addEventListener('keydown', handleGlobalKeyDown);
}

// 设置自动调整输入框高度
function setupAutoResize() {
    elements.messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

// 处理键盘事件
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// 处理全局键盘事件
function handleGlobalKeyDown(e) {
    // Ctrl/Cmd + K: 新对话
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        startNewChat();
    }
    
    // Ctrl/Cmd + L: 聚焦输入框
    if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
        e.preventDefault();
        elements.messageInput.focus();
    }
}

// 更新字符计数
function updateCharCount() {
    const length = elements.messageInput.value.length;
    elements.charCount.textContent = `${length}/2000`;
    
    // 更新发送按钮状态
    elements.sendBtn.disabled = length === 0 || isStreaming;
}

// 发送消息
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || isStreaming) return;

    // 添加用户消息到界面
    addMessageToUI('user', message);
    
    // 清空输入框
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
    updateCharCount();

    // 显示加载指示器
    showLoading();

    try {
        // 创建助手消息容器
        const assistantMessageId = addMessageToUI('assistant', '');
        
        // 发送流式请求
        await streamResponse(message, assistantMessageId);
        
        // 保存到聊天历史
        saveToChatHistory(message);
        
    } catch (error) {
        console.error('发送消息失败:', error);
        addErrorMessage('发送消息时出现错误，请重试。');
    } finally {
        hideLoading();
    }
}

// 流式响应处理
async function streamResponse(message, messageId) {
    const requestData = {
        message: message,
        history: chatHistory,
        system_prompt: elements.systemPrompt.value
    };

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentContent = '';

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'content') {
                            currentContent += data.content;
                            updateMessageContent(messageId, currentContent);
                        } else if (data.type === 'sources') {
                            addSourcesToMessage(messageId, data.sources);
                        } else if (data.type === 'error') {
                            updateMessageContent(messageId, data.content);
                        }
                    } catch (e) {
                        console.error('解析流数据失败:', e);
                    }
                }
            }
        }

    } catch (error) {
        console.error('流式响应错误:', error);
        updateMessageContent(messageId, '抱歉，处理您的请求时出现了错误。请重试。');
    }
}

// 添加消息到UI
function addMessageToUI(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
    if (role === 'user') {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    } else {
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
    }
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.innerHTML = formatMessageContent(content);
    
    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = getCurrentTime();
    
    messageContent.appendChild(messageText);
    messageContent.appendChild(messageTime);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    elements.chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    scrollToBottom();
    
    // 返回消息ID用于后续更新
    return messageDiv.id = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// 更新消息内容
function updateMessageContent(messageId, content) {
    const messageDiv = document.getElementById(messageId);
    if (messageDiv) {
        const messageText = messageDiv.querySelector('.message-text');
        messageText.innerHTML = formatMessageContent(content);
        scrollToBottom();
    }
}

// 格式化消息内容
function formatMessageContent(content) {
    if (!content) return '';
    
    // 处理换行
    content = content.replace(/\n/g, '<br>');
    
    // 处理代码块
    content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang || 'text'}">${code}</code></pre>`;
    });
    
    // 处理行内代码
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // 处理链接
    content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    return content;
}

// 添加源信息到消息
function addSourcesToMessage(messageId, sources) {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv || !sources || sources.length === 0) return;
    
    const sourcesContainer = document.createElement('div');
    sourcesContainer.className = 'sources-container';
    
    const sourcesTitle = document.createElement('div');
    sourcesTitle.className = 'sources-title';
    sourcesTitle.innerHTML = '<i class="fas fa-book"></i> 参考来源';
    
    sourcesContainer.appendChild(sourcesTitle);
    
    sources.forEach(source => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';
        
        sourceItem.innerHTML = `
            <div class="source-title">${source.title}</div>
            <div class="source-content">${source.content}</div>
            <div class="source-score">相关度: ${(source.relevance_score * 100).toFixed(1)}%</div>
        `;
        
        sourcesContainer.appendChild(sourceItem);
    });
    
    const messageContent = messageDiv.querySelector('.message-content');
    messageContent.appendChild(sourcesContainer);
}

// 添加错误消息
function addErrorMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message error';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="message-content">
            <div class="message-text" style="color: #dc2626;">
                ${content}
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示加载指示器
function showLoading() {
    isStreaming = true;
    elements.loadingIndicator.style.display = 'flex';
    elements.sendBtn.disabled = true;
}

// 隐藏加载指示器
function hideLoading() {
    isStreaming = false;
    elements.loadingIndicator.style.display = 'none';
    elements.sendBtn.disabled = false;
}

// 滚动到底部
function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// 获取当前时间
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// 切换侧边栏
function toggleSidebar() {
    elements.sidebar.classList.toggle('show');
}

// 开始新对话
function startNewChat() {
    // 清空聊天界面
    elements.chatMessages.innerHTML = `
        <div class="message assistant-message">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-text">
                    <p>👋 你好！我是RAG智能问答系统，基于检索增强生成技术构建。</p>
                    <p>我可以帮助你：</p>
                    <ul>
                        <li>回答基于知识库的问题</li>
                        <li>提供准确的信息检索</li>
                        <li>支持文档上传和知识库扩展</li>
                    </ul>
                    <p>请开始提问吧！</p>
                </div>
                <div class="message-time">现在</div>
            </div>
        </div>
    `;
    
    // 清空聊天历史
    chatHistory = [];
    currentChatId = null;
    
    // 更新侧边栏
    updateChatHistoryUI();
    
    // 在移动端隐藏侧边栏
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.remove('show');
    }
}

// 保存到聊天历史
function saveToChatHistory(message) {
    const chatId = currentChatId || `chat-${Date.now()}`;
    currentChatId = chatId;
    
    if (!chatHistory.find(chat => chat.id === chatId)) {
        chatHistory.push({
            id: chatId,
            title: message.substring(0, 50) + (message.length > 50 ? '...' : ''),
            timestamp: new Date().toISOString(),
            messages: []
        });
    }
    
    const chat = chatHistory.find(chat => chat.id === chatId);
    chat.messages.push({
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
    });
    
    // 保存到本地存储
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    
    // 更新UI
    updateChatHistoryUI();
}

// 更新聊天历史UI
function updateChatHistoryUI() {
    elements.chatHistory.innerHTML = '';
    
    chatHistory.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-history-item';
        chatItem.textContent = chat.title;
        chatItem.addEventListener('click', () => loadChat(chat.id));
        
        if (chat.id === currentChatId) {
            chatItem.classList.add('active');
        }
        
        elements.chatHistory.appendChild(chatItem);
    });
}

// 加载聊天
function loadChat(chatId) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) return;
    
    currentChatId = chatId;
    
    // 清空当前聊天界面
    elements.chatMessages.innerHTML = '';
    
    // 加载聊天消息
    chat.messages.forEach(msg => {
        addMessageToUI(msg.role, msg.content);
    });
    
    // 更新侧边栏
    updateChatHistoryUI();
    
    // 在移动端隐藏侧边栏
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.remove('show');
    }
}

// 加载聊天历史
function loadChatHistory() {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
        try {
            chatHistory = JSON.parse(saved);
            updateChatHistoryUI();
        } catch (e) {
            console.error('加载聊天历史失败:', e);
        }
    }
}

// 显示设置模态框
function showSettingsModal() {
    elements.settingsModal.classList.add('show');
}

// 隐藏设置模态框
function hideSettingsModal() {
    elements.settingsModal.classList.remove('show');
}

// 处理文件上传
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(`文件上传成功: ${result.message}`);
        } else {
            throw new Error('上传失败');
        }
    } catch (error) {
        console.error('文件上传错误:', error);
        alert('文件上传失败，请重试。');
    }
    
    // 清空文件输入
    event.target.value = '';
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initApp);

// 窗口大小改变时处理响应式
window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
        elements.sidebar.classList.remove('show');
    }
}); 