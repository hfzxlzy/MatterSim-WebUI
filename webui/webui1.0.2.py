# 调用sys和os模块，设置项目根目录为Python路径，以便导入项目内的模块
import sys, os
# 获取当前文件所在目录的上一级目录作为项目根目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 导入WebUI所需框架streamlit库
import streamlit as st
# 导入shutil库用于文件操作，如复制、移动等
import shutil
# 导入mattersim库，获取当前安装的版本号用于显示在页面标题中
import mattersim

# 导入核心模块
from webui.core.sysmonitor import sys_monitor_fragment,log_fragment
from webui.core.history import load_history
from webui.core.env import TMP
# 导入ASE工具相关模块
from webui.ase_tools.viewer import show_structure_viewer_page
from webui.ase_tools.editor import show_structure_editor
from webui.ase_tools.builder import show_structure_builder
# 导入inference功能组件相关模块
from webui.inference.ui import inference_ui
from webui.inference.infer_core import load_addon_plugins
# 导入training功能组件相关模块
from webui.training.ui import show_training_page

# ---------------- Slurm Check ----------------
# 定义函数检查系统中是否安装了Slurm调度器
def slurm_available():
    #通过检查sbatch命令是否可用来判断Slurm是否安装和配置正确
    return shutil.which("sbatch") is not None
# 在侧边栏显示Slurm相关选项，如果检测到Slurm环境，建议用户启用Slurm调度模式以更好地管理HPC资源
if slurm_available():
    # 先创建一个占位符（视觉上在上）
    msg_box = st.sidebar.empty()
    # checkbox 实际上先渲染（但视觉上在下面）
    enable_slurm = st.sidebar.checkbox(
        "启用 Slurm 调度模式",    # 标签文本
        value = False    # 默认不启用
    )
    # 根据 checkbox 的即时值更新提示框（同步刷新）
    if enable_slurm:
        msg_box.success("已启用 Slurm 任务调度模式，作业将通过 Slurm 提交。")
    else:
        msg_box.warning("检测到环境存在 Slurm ，推荐使用 Slurm 调度计算资源，防止影响其他 HPC 用户。")
else:
    enable_slurm = False

# ---------------- Base UI Setup ----------------
# 设置Streamlit页面配置
st.set_page_config(layout="wide", page_title="MatterSim WebUI")
# 获取当前安装的mattersim版本号，用于显示在页面标题中
mattersim_version = mattersim.__version__
# 页面标题
st.title(f"MatterSim(ver.{mattersim_version}) 控制面板")

# 加载插件并注册功能
if not hasattr(st, "_addons_loaded"):
    load_addon_plugins()
    st._addons_loaded = True

# ---------------- Render UI Based on Mode ----------------
# 侧边栏：模式选择
mode = st.sidebar.radio("模式选择", ["推理", "训练", "ASEWeb", "历史记录"])

# 选择ASE模式
if mode == "ASEWeb":
    tabs = st.tabs(["结构查看", "结构编辑", "结构构建"])
    with tabs[0]:
        show_structure_viewer_page()
    with tabs[1]:
        show_structure_editor()
    with tabs[2]:
        show_structure_builder()
    st.stop()

# 选择历史记录模式
if mode == "历史记录":
    history = load_history()
    st.write(history) 
    st.stop()

# ---------------- Create two-column layout ----------------
# 非ASE及历史记录模式创建两列布局(左侧用于主要操作，右侧用于GPU监控)
col_left, col_right = st.columns([2, 1])

# 在右侧列中显示GPU监控界面
with col_right:
    # 调用系统监控组件
    sys_monitor_fragment()
    # 调用日志显示组件
    log_fragment()

# 在左侧列中显示插件运行界面
with col_left:
    
    # 如果启用Slurm调度模式，显示Slurm参数配置界面
    if enable_slurm:
        with st.expander("Slurm 调度参数（点击展开）", expanded=False):
            # 所有输入框都必须在这个缩进层级内
            if "slurm_cfg" not in st.session_state or st.session_state["slurm_cfg"] is None:
                st.session_state["slurm_cfg"] = {
                    "job_name": "mattersimui-task",    # 任务名称固定为 mattersimui-task
                    "partition": "normal",    # 任务分区固定为 normal
                    "cpus": 32,    # 分配cpu数量，默认32   
                    "mem": "64G",    # 分配内存数量，默认64G
                    "time": "02:00:00",    # 分配最长运行时间，默认2小时
                    "gpus": 0,    # 分配GPU数量，默认0（不使用GPU）
                    "nice": 0,    # 优先级固定最高
                    "output_dir": TMP,    # 指定 Slurm 输出文件保存目录，默认使用临时目录
                }
            # 显示输入框让用户调整Slurm参数
            cfg = st.session_state["slurm_cfg"]
            # job_name和partition是固定的，不需要用户输入
            cfg["cpus"] = st.number_input("CPU 数量", min_value=1, max_value=256, value=cfg["cpus"])
            mem_value = st.number_input("内存 (G)", min_value=1, max_value=512, value=int(cfg["mem"].rstrip("G")))
            cfg["mem"] = f"{mem_value}G"
            cfg["gpus"] = st.number_input("GPU 数量", min_value=0, max_value=1, value=cfg["gpus"])
            cfg["time"] = st.text_input("最长运行时间", cfg["time"])
            cfg["output_dir"] = st.text_input("slurm.out 保存目录", cfg["output_dir"])
            # 将更新后的配置保存回 session_state
            st.session_state["slurm_cfg"] = cfg
    # 如果未启用Slurm模式，确保session_state中没有残留的Slurm配置
    else:
        st.session_state["slurm_cfg"] = None

    # 显示mattersim训练模式运行界面
    if mode == "训练":
        # 将slurm_cfg从session_state中获取，传递给训练界面以供使用
        slurm_cfg = st.session_state.get("slurm_cfg", None)
        # 调用training_ui函数显示训练界面
        show_training_page(slurm_cfg)

    # 显示mattersim推理模式运行界面
    elif mode == "推理":
        # 将slurm_cfg从session_state中获取，传递给推理界面以供使用
        slurm_cfg = st.session_state.get("slurm_cfg", None)
        # 调用inference_ui函数显示推理界面
        inference_ui(slurm_cfg)
