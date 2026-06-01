# 运行器模块，负责执行命令并将输出保存到日志缓存中，供sysmonitor读取
import time
import os
import threading
# 调用subprocess模块来执行命令，调用datetime模块来记录时间戳
import subprocess
from datetime import datetime
# 调用utils.history模块中的append_history函数来将新的历史记录追加到历史记录文件中
from webui.core.history import append_history

# 全局日志缓存（sysmonitor 会读取）
log_buffer = []

# 实时读取 slurm-%j.out，遇到 Job finished at: 自动退出
def tail_slurm_output(out_path, tag):
    # 不等待文件生成，直接轮询
    while not os.path.exists(out_path):
        # 文件还未生成，继续等待（每隔0.5秒检查一次）
        time.sleep(0.5)
    # 文件已生成，开始读取
    with open(out_path, "r") as f:
        # 持续读取新内容，直到检测到任务结束标志
        while True:
            # 读取新行，如果没有新行则等待
            line = f.readline()

            if line:
                log_buffer.append(f"[{tag}] {line}")
                # 如果检测到任务结束标志，则退出循环
                if "Job finished at:" in line:
                    break
            else:
                # 文件暂时没有新内容，继续等待（每隔0.25秒检查一次）
                time.sleep(0.25)
    # 任务结束 → 写入历史记录
    append_history(tag, log_buffer[:])


# 本地运行系统命令并将输出写入日志容器
def run_local(cmd, tag):
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

# Slurm 运行系统命令并将输出写入日志容器
def run_slurm(cmd, tag, slurm_cfg):
    # 在运行新命令之前清空日志缓存
    log_buffer.clear()
    # 1. 解析 Slurm 配置
    job_name = slurm_cfg["job_name"]    # 从slurm_cfg中获取任务名称
    partition = slurm_cfg["partition"]    # 从slurm_cfg中获取任务分区
    cpus = slurm_cfg["cpus"]    # 从slurm_cfg中获取分配的CPU数量
    mem = slurm_cfg["mem"]    # 从slurm_cfg中获取分配的内存数量
    time = slurm_cfg["time"]    # 从slurm_cfg中获取任务运行时间
    gpus = slurm_cfg["gpus"]    # 从slurm_cfg中获取分配的GPU数量
    nice = slurm_cfg["nice"]    # 从slurm_cfg中获取任务优先级
    output_dir = slurm_cfg["output_dir"]    # 从slurm_cfg中获取输出目录
    # 2. GPU 行（如果分配了GPU，则添加 --gres=gpu:{gpus} 参数，否则不添加GPU相关参数）
    gpu_line = f"#SBATCH --gres=gpu:{gpus}" if gpus > 0 else ""
    # 3. 生成 sbatch 脚本（路径，使用输出目录和当前时间戳来命名脚本文件，确保每次运行都生成一个唯一的脚本文件）
    script_path = f"{output_dir}/auto_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sh"
    # 生成 sbatch 脚本内容，包含 SBATCH 参数和要执行的命令，脚本中还会输出一些基本的调试信息，如任务开始时间、节点名称、执行的命令、任务结束时间等
    sbatch_script = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={partition}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}
#SBATCH --time={time}
#SBATCH --nice={nice}
#SBATCH --output={output_dir}/slurm-%j.out
{gpu_line}

echo "Job started at: $(date)"
echo "Node: $SLURMD_NODENAME"

# 执行命令
echo "Running command:"
echo "{' '.join(cmd)}"
{' '.join(cmd)}

echo "Job finished at: $(date)"
"""
    # 4. 写入脚本文件
    with open(script_path, "w") as f:
        f.write(sbatch_script)
    # 5. 提交 sbatch
    result = subprocess.run(
        ["sbatch", script_path],
        capture_output=True,
        text=True
    )
    # 将 sbatch 输出添加到日志缓存中，供 sysmonitor 读取
    sbatch_output = result.stdout.strip()
    log_buffer.append(f"[{tag}] 提交 Slurm 任务: {sbatch_output}\n")
    # 6. 解析 JobID
    try:
        # 从 sbatch 输出中提取 JobID，通常是输出的最后一个单词
        jobid = sbatch_output.split()[-1]
        log_buffer.append(f"[{tag}] JobID = {jobid}\n")
        log_buffer.append(f"[{tag}] 输出文件: {output_dir}/slurm-{jobid}.out\n")
        # 启动 tail 线程来实时读取 slurm-%j.out 文件，并将输出写入日志缓存中，直到检测到任务结束标志
        out_path = f"{output_dir}/slurm-{jobid}.out"
        threading.Thread(
            target=tail_slurm_output,
            args=(out_path, tag),
            daemon=True
        ).start()
    except:
        # 无法解析 JobID，可能是 sbatch 提交失败了，直接将 sbatch 输出写入日志缓存中，并提示用户检查 sbatch 输出
        log_buffer.append(f"[{tag}] 无法解析 JobID，请检查 sbatch 输出\n")

    # 7. 返回日志缓存，供 sysmonitor 读取
    return log_buffer

# 统一的命令运行接口，根据是否启用Slurm调度模式来选择运行函数
def run_command(cmd, tag, slurm_cfg=None):
    # 如果存在则使用Slurm运行，则调用 run_slurm 函数，并传入 Slurm 配置参数
    if slurm_cfg is not None:
        # 调用 run_slurm 函数，并传入 Slurm 配置参数
        return run_slurm(cmd, tag, slurm_cfg)
    # 否则本地运行，调用 run_local 函数
    else:
        # 直接调用 run_local 函数
        return run_local(cmd, tag)