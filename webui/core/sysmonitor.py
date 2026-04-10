# 系统性能监控模块
# 调用streamlit库构建系统监控界面
import streamlit as st
# 调用subprocess库执行系统命令获取GPU信息
import subprocess
#，调用psutil库获取CPU和RAM使用情况
import psutil
#调用html库和re库清洗和格式化日志输出，确保在Web界面上正确显示
import html
import re
# 从runner模块中导入日志缓存，实时显示命令输出
from webui.core.runner import log_buffer

# ---------------- SYS Monitor ----------------
# 获取GPU使用信息
def gpu_info():
    #尝试执行命令获取GPU信息
    try:
        #在shell中调用nvidia-smi命令获取GPU利用率和显存使用情况
        out = subprocess.check_output(
            "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total "
            "--format=csv,noheader,nounits",
            shell=True
        ).decode().strip()
        #拆分输出字符串以提取各项指标
        gpu_util, mem_used, mem_total = out.split(", ")
        #返回GPU利用率、显存使用和总量
        return int(gpu_util), int(mem_used), int(mem_total)
    #捕获异常并返回None
    except:
        return None, None, None

#获取CPU、RAM使用信息
def cpu_ram_info():
    #统计当前的cpu使用率
    cpu_util = psutil.cpu_percent(interval=None)
    #获取系统RAM使用情况
    ram = psutil.virtual_memory()
    #转换为MB单位
    ram_used = ram.used // (1024 * 1024)
    ram_total = ram.total // (1024 * 1024)
    #返回CPU和RAM使用率、总量
    return cpu_util, ram_used, ram_total

# 调用碎片组件构建系统监控界面，每秒刷新一次
@st.fragment(run_every=3)
#定义系统监控组件
def sys_monitor_fragment():
    st.subheader("系统监控")
    #调取cpu_ram_info和gpu_info函数获取最新的系统性能数据
    cpu_util, ram_used, ram_total = cpu_ram_info()
    gpu_util, gpu_mem_used, gpu_mem_total = gpu_info()

    #显示CPU和RAM使用情况
    st.metric("CPU 利用率", f"{cpu_util}%")
    st.metric("内存使用", f"{ram_used} / {ram_total} MB")
    #显示GPU使用情况
    if gpu_util is not None:
        st.metric("GPU 利用率", f"{gpu_util}%")
        st.metric("显存使用", f"{gpu_mem_used} / {gpu_mem_total} MB")
    else:
        st.warning("未检测到 GPU")

# 调用碎片组件构建系统监控界面，每秒刷新一次
@st.fragment(run_every=1)
#定义日志显示组件
def log_fragment():
    st.subheader("运行日志")
    #创建一个空的日志显示容器
    #st.text("".join(log_buffer))
    raw_log = "".join(log_buffer)

    # 1. 清洗 ANSI 颜色码（\x1b[31m 等）
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    cleaned = ansi_escape.sub('', raw_log)

    # 2. 清洗所有控制字符（\x00-\x1F 和 \x7F）
    cleaned = re.sub(r'[\x00\x07\x1B\x7F]', '', cleaned)

    # 3. HTML 转义，避免破坏 HTML 结构
    safe = html.escape(cleaned)

    # 4. 渲染深色日志框
    st.markdown(
#css样式定义日志框外观
f"""
<div id="log-box" style="
    height: 800px;
    overflow-y: auto;
    padding: 12px;
    background-color: #0d0d0d;
    color: #e5e5e5;
    border: 1px solid #333;
    border-radius: 6px;
    font-family: monospace;
    font-size: 13px;
    white-space: pre-wrap;
">
<pre style="margin:0; white-space: pre-wrap;">{safe}</pre>
</div>
""",
    unsafe_allow_html=True
    )
