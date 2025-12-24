from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

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
def calculate(expression: str) -> str:
    """计算一个数学表达式的结果。"""
    try:
        result = eval(expression)
        return f"计算结果是：{result}"
    except Exception as e:
        return f"计算出错：{str(e)}"

# 1. 初始化LLM
llm = init_chat_model(model="deepseek-chat")

# 2. 创建Agent
agent = create_agent(
    model=llm,
    tools=[get_weather, calculate],
    system_prompt="你是一个多功能的助手，可以查询天气和进行数学计算。"
)

# 3. 测试多工具调用
user_queries = [
    "北京和上海的天气怎么样？",
    "如果北京气温是25度，上海是28度，那么北京的温度比上海低多少度？"
]

# 4. 执行测试
for query in user_queries:
    print(f"用户: {query}")
    response = agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    print(f"Agent: {response['messages'][-1].content}")
    print("-" * 50)