import asyncio
from langchain_core.utils.pydantic import BaseModel,Field
from langchain.chat_models import init_chat_model
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.agents import create_agent

model = init_chat_model(model='deepseek-chat')
model = ChatDeepSeek(model='deepseek-chat')
# model = ChatOllama(model='qwen2.5:0.5b')

class Address(BaseModel):
    country: str = Field(description='国家')
    shi: str = Field(description='市')
    qu: str = Field(description='区')
    street: str = Field(description='街道')
    name : str = Field(description='姓名')
    phone : str = Field(description='手机号')

# res = model.batch_as_completed([
#     '简要介绍中国历史',
#     '美国成立时间',
#     '日本与中国地历史渊源',
# ])
#

async def run():
    prompt_template = PromptTemplate.from_template("把这个单词{word}翻译成日文、英文和法语")

    inputs = [prompt_template.format(word=i) for i in ['缘分', '螺旋丸', '绿茶']]

    # res = model.abatch_as_completed(inputs)
    res = await model.abatch(inputs)
    for i in res:
        res =  i
        print(res)
    return res


def address_parse(query):
    llm_structured = model.with_structured_output(Address, include_raw=False)
    res = llm_structured.invoke(query)
    return res


if __name__ == '__main__':
    # res = asyncio.run(model.ainvoke("什么是日语"))
    # asyncio.run(run())
    res = address_parse('北京市西城区月坛北小街2号院综合科研办公楼第5层 陈文曲 13261806906')
    print(res)



