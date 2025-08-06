# RAG Chat System - 智能问答系统

一个基于FastAPI和现代Web技术的RAG（检索增强生成）智能问答系统，具有类似DeepSeek的现代化用户界面。

## 功能特性

- 🤖 **智能问答**: 基于RAG技术提供准确的问答服务
- 🌊 **流式响应**: 实时流式输出，提供更好的用户体验
- 📱 **响应式设计**: 支持桌面端和移动端
- 💾 **聊天历史**: 本地存储聊天记录，支持多会话管理
- 📁 **文档上传**: 支持上传文档扩展知识库
- ⚙️ **系统设置**: 可配置系统提示词和流式响应
- 🎨 **现代化UI**: 类似DeepSeek的优雅界面设计

## 技术栈

### 后端
- **FastAPI**: 现代、快速的Python Web框架
- **Uvicorn**: ASGI服务器
- **Pydantic**: 数据验证
- **LangChain**: RAG框架（可扩展）
- **ChromaDB**: 向量数据库（可扩展）

### 前端
- **HTML5**: 语义化标记
- **CSS3**: 现代化样式，支持响应式设计
- **JavaScript (ES6+)**: 原生JavaScript，无框架依赖
- **Font Awesome**: 图标库
- **Inter Font**: 现代字体

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python main.py
```

或者使用uvicorn直接运行：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问应用

打开浏览器访问: http://localhost:8000

## 项目结构

```
my_rag/
├── main.py              # FastAPI主应用
├── requirements.txt     # Python依赖
├── README.md           # 项目说明
├── .gitignore          # Git忽略文件
└── static/             # 静态文件
    ├── index.html      # 主页面
    ├── style.css       # 样式文件
    └── script.js       # JavaScript逻辑
```

## API接口

### 聊天接口
- **POST** `/api/chat` - 流式聊天接口
- **POST** `/api/upload` - 文档上传接口
- **GET** `/api/health` - 健康检查接口

### 请求示例

```javascript
// 发送聊天消息
const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: "什么是RAG技术？",
        history: [],
        system_prompt: "你是一个专业的AI助手"
    })
});
```

## 功能说明

### 1. 流式聊天
- 支持实时流式输出，模拟打字效果
- 自动处理SSE（Server-Sent Events）
- 支持错误处理和重试机制

### 2. 聊天历史
- 本地存储聊天记录
- 支持多会话管理
- 自动保存和恢复

### 3. 文档上传
- 支持PDF、TXT、DOC、DOCX格式
- 文件大小限制和类型验证
- 上传进度提示

### 4. 响应式设计
- 桌面端：侧边栏 + 主内容区
- 移动端：可折叠侧边栏
- 自适应输入框高度

### 5. 键盘快捷键
- `Ctrl/Cmd + K`: 新对话
- `Ctrl/Cmd + L`: 聚焦输入框
- `Enter`: 发送消息
- `Shift + Enter`: 换行

## 自定义配置

### 系统提示词
在设置中可以自定义系统提示词，影响AI助手的回答风格和行为。

### 流式响应
可以开启/关闭流式响应功能，关闭后将一次性返回完整回答。

## 扩展开发

### 添加新的RAG功能

1. 在`main.py`中扩展`RAGSystem`类
2. 添加新的文档处理逻辑
3. 集成向量数据库（如ChromaDB）
4. 添加更多AI模型支持

### 自定义样式

1. 修改`static/style.css`中的样式变量
2. 调整颜色主题和布局
3. 添加新的动画效果

### 添加新功能

1. 在`static/script.js`中添加新的交互逻辑
2. 在`static/index.html`中添加对应的UI元素
3. 在`main.py`中添加对应的API接口

## 部署说明

### 生产环境部署

1. 使用Gunicorn作为WSGI服务器：
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. 配置Nginx反向代理：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. 使用Docker部署：
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 故障排除

### 常见问题

1. **端口被占用**
   - 修改`main.py`中的端口号
   - 或使用`--port`参数指定其他端口

2. **依赖安装失败**
   - 确保Python版本 >= 3.8
   - 使用虚拟环境：`python -m venv venv && source venv/bin/activate`

3. **流式响应不工作**
   - 检查浏览器是否支持SSE
   - 确认网络连接正常

4. **文件上传失败**
   - 检查文件大小限制
   - 确认文件格式支持

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发者。

---

**注意**: 这是一个演示项目，生产环境使用前请进行充分的安全性和性能测试。 