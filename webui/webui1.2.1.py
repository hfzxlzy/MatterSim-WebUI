# 调用sys和os模块，设置项目根目录为Python路径，以便导入项目内的模块
import sys, os
# 获取当前文件所在目录的上一级目录作为项目根目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 导入WebUI所需框架streamlit库
import streamlit as st
# 导入核心模块
from webui.core.sysmonitor import sys_monitor_fragment,log_fragment
from webui.core.history import load_history
# 导入ASE工具相关模块
from webui.ase_tools.viewer import show_structure_viewer_page
from webui.ase_tools.editor import show_structure_editor
from webui.ase_tools.builder import show_structure_builder
# 导入inference功能组件相关模块
from webui.inference.ui import inference_ui
from webui.inference.infer_core import load_addon_plugins
# 导入training功能组件相关模块
from webui.training.ui import show_training_page

# ---------------- Base UI Setup ----------------
# 设置Streamlit页面配置
st.set_page_config(layout="wide", page_title="MatterSim WebUI")

# 页面标题
st.title("MatterSim WebUI 控制面板")

# 加载插件
load_addon_plugins()

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
    # 显示mattersim训练模式运行界面
    if mode == "训练":
        # 调用training_ui函数显示训练界面
        show_training_page()

    # 显示mattersim推理模式运行界面
    elif mode == "推理":
        # 调用inference_ui函数显示推理界面
        inference_ui()
