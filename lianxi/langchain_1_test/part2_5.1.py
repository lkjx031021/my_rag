
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

model = init_chat_model(model='deepseek-chat', model_provider='deepseek', temperature=0.7)


@tool
def get_user_info(user_name):
    """根据用户姓名查询用户信息，返回姓名、年龄、学历"""
    user_info = {
        '张三': ['张三', 19, '小学'],
        '李四': ['李四', 23, '硕士'],
        '王五': ['王五', 33, '博士'],
    }
    return user_info[user_name]


def run_test():
    memory = InMemorySaver()

    agent = create_agent(model, tools=[get_user_info], checkpointer=memory)
    config = {'configurable': {'thread_id': 'user1'}}

    res1 = agent.invoke({"messages": [{"role": "user", "content":'你好，我叫张三'}]},
                        config=config)
    print(res1["messages"][-1].content)
    config2 = {'configurable': {'thread_id': 'user1'}}
    res2 = agent.invoke({"messages":[{"role": "user", "content": "你还知道我是谁吗, 如果你知道请告诉我我的基本信息"}]}, config=config2)
    print(res2["messages"][-1].content)

if __name__ == '__main__':
    run_test()