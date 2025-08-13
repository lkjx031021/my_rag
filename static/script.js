// 全局变量
let chatHistory = [];
let currentChatId = null;
let isStreaming = false;
let authToken = null;

// DOM 元素
const elements = {
    appContainer: document.querySelector('.app-container'),
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
    streamingToggle: document.getElementById('streamingToggle'),
    // 登录/注册相关元素
    loginModal: document.getElementById('loginModal'),
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    loginError: document.getElementById('loginError'),
    registerError: document.getElementById('registerError'),
    logoutBtn: document.getElementById('logoutBtn'),
    currentUser: document.getElementById('currentUser'),
    showRegisterBtn: document.getElementById('show-register'),
    showLoginBtn: document.getElementById('show-login'),
    loginFormContainer: document.getElementById('login-form-container'),
    registerFormContainer: document.getElementById('register-form-container'),
};

// 初始化应用
function initApp() {
    setupEventListeners();
    setupAutoResize();
    checkLoginStatus();
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

    // 登录/注册/登出
    elements.loginForm.addEventListener('submit', handleLogin);
    elements.registerForm.addEventListener('submit', handleRegister);
    elements.logoutBtn.addEventListener('click', handleLogout);
    elements.showRegisterBtn.addEventListener('click', showRegisterForm);
    elements.showLoginBtn.addEventListener('click', showLoginForm);


    // 键盘快捷键
    document.addEventListener('keydown', handleGlobalKeyDown);
}

// --- 认证功能 ---

function showRegisterForm(e) {
    if(e) e.preventDefault();
    elements.loginFormContainer.style.display = 'none';
    elements.registerFormContainer.style.display = 'block';
}

function showLoginForm(e) {
    if(e) e.preventDefault();
    elements.registerFormContainer.style.display = 'none';
    elements.loginFormContainer.style.display = 'block';
}


async function handleRegister(e) {
    e.preventDefault();
    const username = e.target['register-username'].value;
    const password = e.target['register-password'].value;
    elements.registerError.textContent = '';

    try {
        const response = await fetch('/api/users/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        
        if (response.ok) {
            alert('注册成功！现在您可以登录了。');
            showLoginForm();
        } else {
            elements.registerError.textContent = data.message || '注册失败，请重试。';
        }
    } catch (error) {
        elements.registerError.textContent = '发生网络错误，请重试。';
    }
}


function checkLoginStatus() {
    authToken = localStorage.getItem('ragToken');
    if (authToken) {
        // Simple check - just show app with stored username
        showApp({ username: authToken });
    } else {
        showLogin();
    }
}

function showLogin() {
    elements.loginModal.classList.add('show');
    elements.appContainer.classList.add('logged-out');
}

function showApp(user) {
    elements.loginModal.classList.remove('show');
    elements.appContainer.classList.remove('logged-out');
    elements.logoutBtn.style.display = 'flex';
    elements.currentUser.textContent = user.username;
    loadChatHistory();
}

async function handleLogin(e) {
    e.preventDefault();
    const username = e.target['login-username'].value;
    const password = e.target['login-password'].value;
    elements.loginError.textContent = '';

    try {
        const response = await fetch('/api/users/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        
        if (response.ok) {
            authToken = data.username; // Using username as simple auth token
            localStorage.setItem('ragToken', authToken);
            showApp({ username: data.username });
        } else {
            elements.loginError.textContent = data.message || '用户名或密码错误';
        }
    } catch (error) {
        elements.loginError.textContent = '发生网络错误，请重试。';
    }
}

function handleLogout() {
    authToken = null;
    localStorage.removeItem('ragToken');
    elements.logoutBtn.style.display = 'none';
    elements.currentUser.textContent = '';
    chatHistory = [];
    updateChatHistoryUI();
    showLogin();
}

// --- API 请求封装 ---

async function fetchWithAuth(url, options = {}) {
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${authToken}`
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        handleLogout();
        throw new Error('Unauthorized');
    }

    return response;
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

// --- Utility Functions ---
function debounce(func, wait) {
    let timeout;

    const debounced = function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };

    debounced.cancel = function() {
        clearTimeout(timeout);
    };

    return debounced;
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

    addMessageToUI('user', message);
    
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
    updateCharCount();

    showLoading();

    try {
        const assistantMessageId = addMessageToUI('assistant', '');
        await streamResponse(message, assistantMessageId);
        saveToChatHistory(message, assistantMessageId); // Assuming assistantMessageId is not needed here, but the function signature implies it. 
        
    } catch (error) {
        console.error('发送消息失败:', error);
        if (error.message !== 'Unauthorized') {
            addErrorMessage('发送消息时出现错误，请重试。');
        }
    } finally {
        hideLoading();
        updateCharCount();
    }
}

// 流式响应处理
async function streamResponse(message, messageId) {
    try {
        const response = await fetchWithAuth('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
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
                if (!line.trim()) continue; // 跳过空行
                
                try {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6).trim();
                        if (!jsonStr) continue; // 跳过空数据
                        
                        console.log('原始SSE数据:', jsonStr); // 调试日志
                        
                        const data = JSON.parse(jsonStr);
                        console.log('解析后数据:', data); // 调试日志
                        
                        if (data.text) {
                            currentContent += data.text;
                            updateMessageContent(messageId, currentContent, true);
                            await new Promise(resolve => setTimeout(resolve, 10));
                        } else if (data.type === 'error') {
                            currentContent = data.text || data.content || '处理请求时出错';
                            updateMessageContent(messageId, currentContent, false);
                            break;
                        }
                    }
                } catch (e) {
                    console.error('解析SSE数据失败:', e, '原始数据:', line);
                    // 不中断流程，继续处理后续数据
                }
            }
        }

        // 更新聊天历史
        const chat = chatHistory.find(c => c.id === currentChatId);
        if (chat) {
            const lastMessage = chat.messages[chat.messages.length - 1];
            if (lastMessage && lastMessage.role === 'assistant') {
                lastMessage.content = currentContent;
                localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
            }
        }
    } catch (error) {
        console.error('流式响应错误:', error);
        updateMessageContent(messageId, '抱歉，处理您的请求时出现了错误。请重试。', true);
        throw error;
    }
}

// 添加消息到UI
function addMessageToUI(role, content) {
    const messageDiv = document.createElement('div');
    const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    messageDiv.id = messageId;
    messageDiv.className = `message ${role}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

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

    if (window.MathJax && window.MathJax.typeset) {
        window.MathJax.startup.promise.then(() => {
            window.MathJax.typesetPromise([messageText]).catch((err) => console.warn('公式渲染失败:', err));
        });
    }

    scrollToBottom();
    return messageId;
}

// 更新消息内容
function updateMessageContent(messageId, content, needsRender = false) {
    const messageDiv = document.getElementById(messageId);
    if (messageDiv) {
        const messageText = messageDiv.querySelector('.message-text');
        messageText.innerHTML = formatMessageContent(content);
        
        if (needsRender) {
            // 代码高亮
            if (window.Prism) {
                Prism.highlightAllUnder(messageDiv);
            }
            
            // 数学公式渲染
            if (window.MathJax) {
                try {
                    // 确保MathJax已加载
                    if (window.MathJax.typesetPromise) {
                        window.MathJax.typesetPromise([messageText]).catch(err => {
                            console.warn('MathJax渲染失败:', err);
                            // 重试渲染
                            setTimeout(() => {
                                if (window.MathJax.typesetPromise) {
                                    window.MathJax.typesetPromise([messageText]);
                                }
                            }, 500);
                        });
                    } else {
                        // 如果MathJax未完全加载，等待后重试
                        setTimeout(() => {
                            if (window.MathJax.typesetPromise) {
                                window.MathJax.typesetPromise([messageText]);
                            }
                        }, 1000);
                    }
                } catch (err) {
                    console.error('MathJax渲染错误:', err);
                }
            }
        }
        
        scrollToBottom();
    }
}

// 格式化消息内容
function formatMessageContent(content) {
    if (!content) return '';
    
    try {
        // 更强大的数学公式匹配正则表达式
        const mathRegex = /(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$(?!\w))/g;
        const mathBlocks = [];
        
        // 保护数学公式不被marked.js处理
        let tempContent = content.replace(mathRegex, (match) => {
            const placeholder = `__MATHJAX_PLACEHOLDER_${mathBlocks.length}__`;
            mathBlocks.push(match);
            return placeholder;
        });

        // 配置marked.js
        marked.setOptions({
            breaks: true,
            gfm: true,
            smartLists: true,
            smartypants: true,
            sanitize: false,
            highlight: function(code, lang) {
                if (lang && Prism.languages[lang]) {
                    try {
                        return Prism.highlight(code, Prism.languages[lang], lang);
                    } catch (err) { console.warn('代码高亮失败:', err); }
                }
                return code;
            },
            // 添加数学公式扩展
            extensions: {
                math: {
                    // 启用内联公式
                    inlineMath: { 
                        open: '$', 
                        close: '$', 
                        latex: false 
                    },
                    // 启用块级公式
                    displayMath: { 
                        open: '$$', 
                        close: '$$', 
                        latex: true 
                    }
                }
            }
        });
        
        // 解析Markdown
        let html = marked.parse(tempContent);
        
        // 恢复数学公式
        html = html.replace(/__MATHJAX_PLACEHOLDER_(\d+)__/g, (match, index) => {
            return mathBlocks[parseInt(index, 10)];
        });
        
        // 特别处理数学公式，确保MathJax正确渲染
        html = html.replace(/<formula>(.*?)<\/formula>/g, (match, p1) => {
            return `<span class="math">$${p1}$$</span>`;
        });
        
        // 确保代码块有正确的语言类
        html = html.replace(/<pre><code class="language-(\w+)">/g, '<pre><code class="language-$1">');
        html = html.replace(/<pre><code>/g, '<pre><code class="language-text">');
        
        return html;
    } catch (error) {
        console.error('Markdown解析失败:', error);
        return content.replace(/\n/g, '<br>');
    }
}

// 添加错误消息
function addErrorMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message error';
    messageDiv.innerHTML = `
        <div class="message-avatar"><i class="fas fa-exclamation-triangle"></i></div>
        <div class="message-content">
            <div class="message-text" style="color: #dc2626;">${content}</div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示/隐藏加载指示器
function showLoading() {
    isStreaming = true;
    elements.loadingIndicator.style.display = 'flex';
    elements.sendBtn.disabled = true;
}

function hideLoading() {
    isStreaming = false;
    elements.loadingIndicator.style.display = 'none';
    updateCharCount();
}

// 滚动到底部
function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// 获取当前时间
function getCurrentTime() {
    return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

// 切换侧边栏
function toggleSidebar() {
    elements.sidebar.classList.toggle('show');
}

// 开始新对话
function startNewChat() {
    elements.chatMessages.innerHTML = `
        <div class="message assistant-message">
            <div class="message-avatar"><i class="fas fa-robot"></i></div>
            <div class="message-content">
                <div class="message-text">
                    <p>👋 你好！我是RAG智能问答系统。请开始提问吧！</p>
                </div>
                <div class="message-time">现在</div>
            </div>
        </div>
    `;
    
    currentChatId = null;
    updateChatHistoryUI();
    
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.remove('show');
    }
}

// 保存到聊天历史
function saveToChatHistory(userMessage, assistantMessageId) { // assistantMessageId is unused in this function
    const chatId = currentChatId || `chat-${Date.now()}`;
    
    if (!currentChatId) {
        currentChatId = chatId;
        chatHistory.push({
            id: chatId,
            title: userMessage.substring(0, 40) + (userMessage.length > 40 ? '...' : ''),
            timestamp: new Date().toISOString(),
            messages: []
        });
    }
    
    const chat = chatHistory.find(chat => chat.id === chatId);
    chat.messages.push({
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString()
    });
    // Add a placeholder for the assistant message
    chat.messages.push({
        role: 'assistant',
        content: '', // This will be updated when the stream ends
        timestamp: new Date().toISOString()
    });
    
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    updateChatHistoryUI();
}

// 更新聊天历史UI
function updateChatHistoryUI() {
    elements.chatHistory.innerHTML = '';
    chatHistory.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
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
    elements.chatMessages.innerHTML = '';
    
    chat.messages.forEach(msg => {
        addMessageToUI(msg.role, msg.content);
    });
    
    updateChatHistoryUI();
    
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
            chatHistory = [];
        }
    }
}

// 显示/隐藏设置模态框
function showSettingsModal() {
    elements.settingsModal.classList.add('show');
}

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
        const response = await fetchWithAuth('/api/upload', {
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
        if (error.message !== 'Unauthorized') {
            alert('文件上传失败，请重试。');
        }
    }
    
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
