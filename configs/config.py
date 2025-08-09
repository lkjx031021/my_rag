import yaml
import os

def load_db_config():
    """
    加载并解析 db.yaml 配置文件。

    Returns:
        dict: 包含数据库配置的字典，如果文件不存在或格式错误则返回空字典。
    """
    # 获取当前脚本 (config.py) 所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建到 db.yaml 的路径
    db_yaml_path = os.path.join(current_dir, 'db.yaml')
    
    if not os.path.exists(db_yaml_path):
        # 或者可以引发一个异常
        return {}

    with open(db_yaml_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    return config.get('db', {})

class Cfg():

    def __init__(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建到 db.yaml 的路径
        db_yaml_path = os.path.join(current_dir, 'db.yaml')
        with open(db_yaml_path, 'r', encoding='utf-8') as file:
            self.cfg = yaml.safe_load(file)

cfg = Cfg().cfg
# --- 使用示例 ---
# 如果直接运行此文件，则打印数据库配置
if __name__ == '__main__':
    db_settings = load_db_config()
    if db_settings:
        print("数据库配置加载成功:")
        print(f"  用户: {db_settings.get('username')}")
        print(f"  主机: {db_settings.get('hostname')}")
        print(f"  数据库名: {db_settings.get('database_name')}")
        # 注意：在生产环境中不建议打印密码
        # print(f"  密码: {db_settings.get('password')}")
    else:
        print("未能加载数据库配置。")
