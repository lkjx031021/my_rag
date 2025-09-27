import aiohttp
from langchain_ollama import OllamaEmbeddings

OLLAMA_BASE_URL = "http://localhost:11434"
model_name = "embeddinggemma:latest"
# model_name = "bge-m3:latest"  # This model doesn't support embeddings
input_text = ["今天天气不错，挺风和日丽的"]
async def get_embedding():
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={
                "model": model_name,
                "input": input_text  # 使用 input 而不是 prompt
            }
        ) as response:
            result = await response.json()
            # Ollama embed API 返回格式为 {"embeddings": [[...], ...]}
            print(result)
            return result["embeddings"][0]  # 返回第一个向量

# 使用 asyncio 运行异步函数
import asyncio
embedding_result = asyncio.run(get_embedding())
print(embedding_result)
