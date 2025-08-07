#!/usr/bin/env python3
"""
RAG Chat System 启动脚本
"""

import uvicorn
import sys
import os

from fastapi import FastAPI

app = FastAPI()



def main():
    """主函数"""
    print("🚀 启动 RAG Chat System...")
    print("📖 访问地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("🔄 按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 