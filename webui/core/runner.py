# 运行器模块，负责执行命令并将输出保存到日志缓存中，供sysmonitor读取
# 调用subprocess模块来执行命令，调用datetime模块来记录时间戳
import subprocess
from datetime import datetime
# 调用utils.history模块中的append_history函数来将新的历史记录追加到历史记录文件中
from webui.core.history import append_history

# 全局日志缓存（sysmonitor 会读取）
log_buffer = []

# 运行系统命令并将输出写入日志容器
def run_command(cmd, tag):
    # 在运行新命令之前清空日志缓存
    log_buffer.clear()
    # 运行后台线程以执行命令
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    # 实时读取命令输出并将其写入日志缓存
    for line in process.stdout:
        # 将每行输出添加到日志缓存中，并在前面加上时间戳和tag
        log_buffer.append(f"[{tag}] {line}")
    process.wait()
    # 在命令执行完成后，将结束信息添加到日志缓存中，并记录退出码
    log_buffer.append(f"\n[{tag}] 任务结束，退出码 {process.returncode}\n")

    # 将日志缓存中的内容追加到历史记录文件中，使用当前时间戳和模式tag
    append_history(tag, log_buffer[:])
    return log_buffer
