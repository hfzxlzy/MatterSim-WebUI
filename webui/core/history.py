# 历史记录模块，用于记录用户的操作历史，包括时间戳、模式tag和cmd输出内容
# 调用OS库和datetime模块来处理文件和时间
import os
from datetime import datetime
# 调用json库来处理历史记录的存储和读取
import json
# 从环境变量中获取历史记录文件的路径
from webui.core.env import HISTORY_FILE

# 加载历史记录
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

# 保存历史记录
def save_history(h):
    json.dump(h, open(HISTORY_FILE, "w"), indent=2)
    
# 将新的历史记录追加到历史记录文件中，定义变量mode表示当前模式tag，lines表示输出行的内容
def append_history(mode, lines):
    history = load_history()
    # 将新的历史记录追加到历史记录列表中，并保存到文件中
    history.append({
        # 记录当前时间戳
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # 记录模式tag
        "mode": mode,
        # 记录输出行的内容
        "lines": lines
    })
    with open(HISTORY_FILE, "w") as f:
        # 将历史记录列表以JSON格式写入文件中，使用缩进格式化输出
        json.dump(history, f, indent=2)

