// 全局变量
let chatHistory = [];
let currentChatId = null;
let isStreaming = false;
let authToken = null;

// DOM 元素
const conversationElements = {
    chatHistory: document.getElementById('chatHistory'),
    chatMessages: document.getElementById('chatMessages'),
    newChatBtn: document.getElementById('newChatBtn'),
    sidebar: document.getElementById('sidebar'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    loadingIndicator: document.getElementById('loadingIndicator'),
    charCount: document.getElementById('charCount')
};

// 初始化会话功能
function initConversation() {
    // 如果没有当前聊天ID，获取用户对话列表
    if (!currentChatId) {
        loadUserConversations();
    }
    
    // 设置事件监听器
    setupConversationEventListeners();
}

// 设置事件监听器
function setupConversationEventListeners() {
    // 新对话按钮点击事件
    conversationElements.newChatBtn.addEventListener('click', startNewChat);
    
    // 输入框内容变化事件
    conversationElements.messageInput.addEventListener('input', updateCharCount);
    
    // 发送按钮点击事件
    conversationElements.sendBtn.addEventListener('click', sendMessage);
    
    // 回车键发送消息
    conversationElements.messageInput.addEventListener('keydown', handleKeyDown);
}

// 获取用户对话列表
async function loadUserConversations() {
    try {
        const response = await fetchWithAuth('/api/conversations', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            params: {
                user_id: authToken,
                chat_types: 'text' // 默认获取文本对话
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            chatHistory = data.data || [];
            updateChatHistoryUI();
            
            // 如果有对话记录，加载最近的对话
            if (chatHistory.length > 0) {
                loadChat(chatHistory[0].id);
            }
        } else {
            throw new Error('获取对话列表失败');
        }
    } catch (error) {
        console.error('加载对话列表时出错:', error);
        addErrorMessage('无法加载对话列表，请重试。');
    }
}

// 更新对话历史UI
function updateChatHistoryUI() {
    // 清空现有内容
    conversationElements.chatHistory.innerHTML = '';
    
    // 按时间排序
    chatHistory.sort((a, b) => new Date(b.create_time) - new Date(a.create_time));
    
    // 添加每个对话项
    chatHistory.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-history-item';
        chatItem.textContent = chat.name || '新对话';
        chatItem.addEventListener('click', () => loadChat(chat.id));
        
        if (chat.id === currentChatId) {
            chatItem.classList.add('active');
        }
        
        conversationElements.chatHistory.appendChild(chatItem);
    });
}

// 加载特定对话
async function loadChat(chatId) {
    try {
        const response = await fetchWithAuth(`/api/conversations/messages`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            params: {
                conversation_id: chatId
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const messages = data.data || [];
            
            // 更新当前对话ID
            currentChatId = chatId;
            
            // 更新UI
            conversationElements.chatMessages.innerHTML = '';
            
            // 显示每条消息
            messages.forEach(msg => {
                addMessageToUI(msg.chat_type === 'user' ? 'user' : 'assistant', msg.query || msg.response || '');
            });
            
            // 更新侧边栏高亮
            updateChatHistoryUI();
            
            // 滚动到底部
            scrollToBottom();
            
            // 如果是移动端，关闭侧边栏
            if (window.innerWidth <= 768) {
                conversationElements.sidebar.classList.remove('show');
            }
        } else {
            throw new Error('加载对话记录失败');
        }
    } catch (error) {
        console.error('加载对话记录时出错:', error);
        addErrorMessage('无法加载对话记录，请重试。');
    }
}

// 开始新对话
async function startNewChat() {
    try {
        const response = await fetchWithAuth('/api/conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: authToken,
                name: '新对话',
                chat_type: 'text'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const newChatId = data.id;
            
            // 创建新的对话对象
            const newChat = {
                id: newChatId,
                name: '新对话',
                chat_type: 'text',
                create_time: new Date().toISOString()
            };
            
            // 添加到对话历史
            chatHistory.unshift(newChat);
            
            // 加载新对话
            loadChat(newChatId);
            
            // 更新UI
            updateChatHistoryUI();
        } else {
            throw new Error('创建新对话失败');
        }
    } catch (error) {
        console.error('创建新对话时出错:', error);
        addErrorMessage('无法创建新对话，请重试。');
    }
}

// 发送消息
async function sendMessage() {
    const message = conversationElements.messageInput.value.trim();
    if (!message || isStreaming) return;

    // 如果没有当前对话ID，先创建新对话
    if (!currentChatId) {
        await startNewChat();
    }

    // 添加用户消息到UI
    addMessageToUI('user', message);
    
    // 清空输入框
    conversationElements.messageInput.value = '';
    conversationElements.messageInput.style.height = 'auto';
    updateCharCount();

    // 显示加载指示器
    showLoading();

    try {
        // 添加助手消息占位符
        const assistantMessageId = addMessageToUI('assistant', '');
        
        // 发送请求并获取流式响应
        await streamResponse(message, assistantMessageId);
        
        // // 保存到聊天历史
        // saveToChatHistory(message, assistantMessageId); 
    } catch (error) {
        console.error('发送消息失败:', error);
        if (error.message !== 'Unauthorized') {
            addErrorMessage('发送消息时出现错误，请重试。');
        }
    } finally {
        // 隐藏加载指示器
        hideLoading();
        
        // 更新字符计数
        updateCharCount();
    }
}

// 流式响应处理
async function streamResponse(message, messageId) {
    try {
        const response = await fetchWithAuth('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: message,
                conversation_id: currentChatId
            })
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
                        
                        const data = JSON.parse(jsonStr);
                        
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
                }
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
    conversationElements.chatMessages.appendChild(messageDiv);

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
                    if (window.MathJax.typesetPromise) {
                        window.MathJax.typesetPromise([messageText]).catch(err => {
                            console.warn('MathJax渲染失败:', err);
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
    conversationElements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// 显示/隐藏加载指示器
function showLoading() {
    isStreaming = true;
    conversationElements.loadingIndicator.style.display = 'flex';
    conversationElements.sendBtn.disabled = true;
}

function hideLoading() {
    isStreaming = false;
    conversationElements.loadingIndicator.style.display = 'none';
    updateCharCount();
}

// 滚动到底部
function scrollToBottom() {
    conversationElements.chatMessages.scrollTop = conversationElements.chatMessages.scrollHeight;
}

// 获取当前时间
function getCurrentTime() {
    return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

// 保存到聊天历史
function saveToChatHistory(userMessage, assistantMessageId) {
    const chatId = currentChatId;
    
    // 如果没有当前聊天ID，表示是新对话
    if (!chatId) {
        currentChatId = `chat-${Date.now()}`;
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
    // 添加占位符作为助手消息
    chat.messages.push({
        role: 'assistant',
        content: '', // 这个将被更新
        timestamp: new Date().toISOString()
    });
    
    // 保存到本地存储
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    updateChatHistoryUI();
}

// 键盘事件处理
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// 显示/隐藏侧边栏
function toggleSidebar() {
    conversationElements.sidebar.classList.toggle('show');
}

// 更新字符计数
function updateCharCount() {
    const length = conversationElements.messageInput.value.length;
    conversationElements.charCount.textContent = `${length}/2000`;
    
    // 更新发送按钮状态
    conversationElements.sendBtn.disabled = length === 0 || isStreaming;
}

// 全局函数
window.sendMessage = sendMessage;
window.toggleSidebar = toggleSidebar;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 获取当前用户ID（假设已登录）
    authToken = localStorage.getItem('userId');

    // 初始化会话功能
    initConversation();
    
    // 如果没有认证令牌，直接返回
    if (!authToken) return;
    
    // 如果没有当前聊天ID，获取用户对话列表
    if (!currentChatId) {
        loadUserConversations();
    } else {
        // 如果已有聊天ID，加载该聊天
        loadChat(currentChatId);
    }
    
    // 创建新会话按钮点击事件
    conversationElements.newChatBtn.addEventListener('click', () => {
        startNewChat();
    });
});

// 窗口大小改变时处理响应式
window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
        conversationElements.sidebar.classList.remove('show');
    }
});
