import getpass
import operator
from typing import Annotated, List, Union
import os

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

# 引入 UI 库
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

# 初始化控制台
console = Console()

# --- 第一步：定义工具 (和以前一样，这是 Core 标准) ---
# 定义天气查询工具
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。"""
    weather_data = {
        "北京": "晴朗，气温25°C",
        "上海": "多云，气温28°C",
        "广州": "小雨，气温30°C"
    }
    return f"{city}的天气是：{weather_data.get(city, '未知')}"

# 定义数学计算工具
@tool
def add(a: float, b: float) -> float:
    """计算两个数的和"""
    return a + b

tools = [get_weather, add]

# --- 第二步：初始化模型 (必须绑定工具) ---
model = init_chat_model(model="deepseek-chat")

# --- 第三步：构建图 (使用 prebuilt 的 ReAct Agent) ---
# 在 LangChain 1.0+ 中，这是 AgentExecutor 的官方替代品
# 它自动构建了：State -> Model Node -> Tool Node -> Loop 逻辑
graph = create_agent(model, tools=tools)

# --- 第四步：编写“教学专用”的可视化流式运行器 ---
def run_demo_with_visualization(user_input: str):
    print("\n" + "="*50)
    console.print(f"[bold yellow]开始任务：[/bold yellow] {user_input}")

    messages = [HumanMessage(content=user_input)]

    # graph.stream 是 LangGraph 的核心
    # 它可以让我们看到状态流转的每一步 (step-by-step)
    step_count = 1

    # values 模式会返回当前的 message 列表状态
    for event in graph.stream({"messages": messages}, stream_mode="values"):
        # 获取最新的一条消息
        current_message = event["messages"][-1]

        # 1. 如果是人类的消息 (初始状态)
        if isinstance(current_message, HumanMessage):
            continue # 跳过，这是输入

        # 2. 如果是 AI 的消息 (思考与决策)
        if isinstance(current_message, AIMessage):
            # 检查是否有工具调用
            if current_message.tool_calls:
                # 提取工具调用的细节
                for tool_call in current_message.tool_calls:
                    console.print(Panel(
                        Text(f"🤔 AI 思考决定：需要调用外部工具\n"
                             f"🔧 工具名称: {tool_call['name']}\n"
                             f"📥 输入参数: {tool_call['args']}", style="bold cyan"),
                        title=f"Step {step_count}: 决策 (Decision)",
                        border_style="cyan"
                    ))
            else:
                # 如果没有工具调用，说明是最终回复
                console.print(Panel(
                    Markdown(current_message.content),
                    title=f"Step {step_count}: 最终回复 (Final Answer)",
                    border_style="green"
                ))
            step_count += 1

        # 3. 如果是工具的消息 (观察与结果)
        if isinstance(current_message, ToolMessage):
            console.print(Panel(
                Text(f"👀 工具返回结果 (Observation):\n{current_message.content}", style="italic white"),
                title=f"Step {step_count}: 执行与观察",
                border_style="magenta"
            ))
            step_count += 1

# --- 第五步：运行演示 ---
if __name__ == "__main__":
    # 这是一个多步任务：先算乘法，再查属性
    run_demo_with_visualization("查询一下北京和上海气温，并且计算一下北京的温度比上海低多少度？")