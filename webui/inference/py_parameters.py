# addons要求的参数定义模块，包含一些基础参数和UI组件的定义
# 调用streamlit库
import streamlit as st

#额外参数UI生成函数
def render_plugin_parameters(plugin):
    params = plugin.get_extra_parameters()

    if not params:
        return

    st.markdown("### 插件参数")

    for key, cfg in params.items():
        full_key = plugin.param_key(key)
        ptype = cfg["type"]
        label = cfg["label"]
        default = cfg.get("default")

        # --- 数字输入 ---
        if ptype == "number":
            st.number_input(
                label,
                min_value=cfg.get("min"),
                max_value=cfg.get("max"),
                value=st.session_state.get(full_key, default),
                step=cfg.get("step", 1),
                key=full_key,
                on_change=lambda: st.session_state.__setitem__("need_update", True)
            )

        # --- 文本输入 ---
        elif ptype == "text":
            st.text_input(
                label,
                value=st.session_state.get(full_key, default),
                key=full_key,
                on_change=lambda: st.session_state.__setitem__("need_update", True)
            )

        # --- 下拉选择 ---
        elif ptype == "select":
            options = cfg["options"]
            default_index = options.index(default) if default in options else 0

            st.selectbox(
                label,
                options,
                index=default_index,
                key=full_key,
                on_change=lambda: st.session_state.__setitem__("need_update", True)
            )

        # --- 复选框 ---
        elif ptype == "checkbox":
            st.checkbox(
                label,
                value=st.session_state.get(full_key, default),
                key=full_key,
                on_change=lambda: st.session_state.__setitem__("need_update", True)
            )
