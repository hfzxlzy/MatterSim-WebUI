# 脚本生成器模块
# 调用streamlit库进行界面交互
import streamlit as st
# 包含脚本生成器的注册和基础组件定义
from webui.inference.infer_core import SCRIPT_REGISTRY
from webui.inference.py_common import COMMON_HANDER

#脚本整合输出函数
def generate_script(state, mode):
    if mode not in SCRIPT_REGISTRY:
        return COMMON_HANDER + f"# 未知模式：{mode}\n"

    handler = SCRIPT_REGISTRY[mode]
    return handler.generate(state)

#脚本更新函数
def update_script():
    # 1. 永远使用最新的模式
    mode = st.session_state.current_mode
    # 2. 让插件决定结构输入模式（关键修复）
    plugin = SCRIPT_REGISTRY[mode]
    # 检查插件参数是否已经写入 session_state
    for key in plugin.get_extra_parameters().keys():
        full_key = plugin.param_key(key)
        if full_key not in st.session_state:
            return  # 参数还没准备好，不生成脚本
    st.session_state.structure_mode = plugin.supported_structure_mode
    # 3. 生成脚本
    st.session_state.generated_script = generate_script(st.session_state, mode)
    # 4. 同步到编辑器
    st.session_state.generated_script_editor = st.session_state.generated_script

