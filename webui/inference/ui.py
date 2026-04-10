# 推理模式基本ui
# 调用streamlit库进行界面设计，torch库进行模型推理，threading库进行多线程处理
import streamlit as st
import torch
import threading
# 调用核心运行函数和环境配置
from webui.core.runner import run_command
from webui.core.env import SIM_ENV_PYTHON
# 调用脚本生成器和结构输入组件
from webui.inference.py_structure import structure_input_block
from webui.inference.py_parameters import render_plugin_parameters
from webui.inference.py_script import update_script
from webui.inference.infer_core import SCRIPT_REGISTRY

def inference_ui():
    st.subheader("推理模式选择")

    tab_view, tab_convert = st.tabs(["构建脚本", "导入脚本"])

    # ============================================================
    #  TAB 1：导入 py 脚本
    # ============================================================
    with tab_view:
        st.subheader("导入并运行 Python 脚本")

        # 1. 上传脚本（可选）
        uploaded_py = st.file_uploader(
            "上传 Python 脚本 (.py，可选)", 
            type=["py"], 
            key="upload_py"
        )

        # 2. 如果上传了脚本 → 自动填充
        if uploaded_py:
            default_code = uploaded_py.read().decode("utf-8")
        else:
            # 如果之前编辑过，保持内容不丢失
            default_code = st.session_state.get("uploaded_code_editor", "")

        # 3. 输入框永远常驻
        edited_code = st.text_area(
            "脚本预览（可编辑）",
            default_code,
            height=400,
            key="uploaded_code_editor"
        )

        # 4. 运行脚本
        if st.button("运行脚本", key="run_uploaded_script"):
            script_path = "/tmp/mattersim_uploaded.py"
            with open(script_path, "w") as f:
                f.write(edited_code)

            cmd = [SIM_ENV_PYTHON, script_path]

            threading.Thread(
                target=run_command,
                args=(cmd, "INFER"),
                daemon=True
            ).start()

            st.success("脚本已开始运行，请查看日志输出。")

    # ============================================================
    #  TAB 2：构建 py 脚本
    # ============================================================
    with tab_convert:
        st.subheader("根据参数构建 Python 脚本")
        #初始化会话
        if 'generated_script' not in st.session_state:
            st.session_state.generated_script = ""
        # -----------------------------
        # 全局参数区
        # -----------------------------
        st.markdown("### 全局参数")
        # 自动检测设备
        default_device = "cuda" if torch.cuda.is_available() else "cpu"
        cola, colb, colc = st.columns([4, 1, 3])
        with cola:
            #模型选择
            st.session_state.model=st.selectbox(
                #[显示名称]
                "模型调用",
                #help=[帮助信息]
                help="可从下拉列表中选择要使用的模型，或输入自定义模型路径，默认为None",
                #options=[选项列表]
                options=["/your/path/of/MatterSim/models/mattersim-v1.0.0-1M.pth", "/your/path/of/MatterSim/models/mattersim-v1.0.0-5M.pth"],
                #index=[默认选项索引]
                index=None,
                #placeholder=[占位符]
                placeholder="选择要使用的模型或输入模型路径",
                #accept_new_options=[是否接受新选项]
                accept_new_options=True,
                key="global_model",
                on_change=lambda: st.session_state.__setitem__("need_update", True)
            )
        with colb:
            #设备选择
            st.session_state.device=st.selectbox(
                #[显示名称]
                "运算设备",
                #help=[帮助信息]
                help="选择运行设备，默认为自动检测的设备类型，GPU优先",
                #options=[选项列表]
                options=["cuda", "cpu"],
                #index=[默认选项索引]
                index=0 if default_device =="cuda" else 1,
                key="global_device",
                on_change=lambda: st.session_state.__setitem__("need_update", True)
            )
        with colc:
            #预设模式
            mode = st.selectbox(
                "选择计算模式",
                list(SCRIPT_REGISTRY.keys()),
                key="current_mode",
                on_change=lambda: st.session_state.__setitem__("need_update", True)
            )

        #结构输入
        file_list= structure_input_block("script_input")
        st.session_state.file_list = file_list

        # 当前插件
        plugin = SCRIPT_REGISTRY[mode]
        # 显示插件标题
        st.subheader(f"{mode} 模式参数")
        # 插件参数（自动渲染）
        render_plugin_parameters(plugin)
        # 实时更新脚本
        update_script()

        # -----------------------------
        # 显示脚本 + 运行
        # -----------------------------
        st.subheader("脚本预览")
        edited_script = st.text_area(
            "可编辑脚本",
            value=st.session_state.generated_script,
            height=400,
            key="generated_script_editor"
        )
        if st.button("运行脚本", key="run_generated_script"):
            script_path = "/tmp/mattersim_generated.py"
            with open(script_path, "w") as f:
                f.write(edited_script)

            cmd = [SIM_ENV_PYTHON, script_path]
            threading.Thread(
                target=run_command,
                args=(cmd, "INFER"),
                daemon=True
            ).start()
            st.success("脚本已开始运行，请查看日志输出。")