# 训练执行模块
# 调用time库获取当前时间
import time
# 调用threading库实现训练过程的多线程执行
import threading
# 调用runner模块中的函数执行训练命令
from webui.core.runner import run_command
from webui.core.history import load_history, save_history

# 训练执行函数
def start_training(cmd, model):
    # 记录训练任务到历史记录
    history = load_history()
    # 将新的训练任务追加到历史记录列表中，包含模式tag、模型信息和时间戳
    history.append({"mode": "train", "model": model, "time": time.time()})
    # 将更新后的历史记录保存到文件中
    save_history(history)
    # 启动后台线程运行训练命令，使用“TRAIN”作为模式tag
    threading.Thread(target=run_command, args=(cmd, "TRAIN"), daemon=True).start()