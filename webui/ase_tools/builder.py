# ASE结构构建模块
# 调用streamlit库构建结构构建界面
import streamlit as st
# 调用io库处理文件输入输出
from io import StringIO
# 调用ase库构建晶体结构
from ase.build import bulk
# 调用render模块中的函数渲染结构和相关信息
from webui.ase_tools.render import render_structure_with_info

# 结构构建组件
def show_structure_builder():
    st.header("结构构建")
    col4, col5, col6 = st.columns([1, 1, 1])
    with col4:
        element = st.text_input("元素符号", "Si")
    with col5:
        crystal = st.selectbox("晶体结构", ["diamond", "fcc", "bcc", "hcp"])
    with col6:
        a = st.number_input("晶格常数 a", value=5.43)

    # 生成晶体结构
    if st.button("生成晶体结构"):
        st.session_state["builder_atoms"] = bulk(element, crystal, a=a)

    if "builder_atoms" in st.session_state:
        with st.expander("展示/收起晶体结构", expanded=True):
            render_structure_with_info(
                st.session_state["builder_atoms"],
                title="生成的晶体结构",
                prefix="builder"
            )
            st.subheader("导出结构")
            fmt = st.selectbox("选择导出格式", ["xyz", "cif", "vasp"], key="builder_export_fmt")

            buf = StringIO()
            st.session_state["builder_atoms"].write(buf, format=fmt)

            st.download_button(
            "下载文件",
            buf.getvalue(),
            file_name=f"builder_output.{fmt}",
            mime="text/plain",
            key="builder_export_btn"
            )

    st.subheader("创建超胞")
    col7, col8, col9 = st.columns([1, 1, 1])
    with col7:
        nx = st.number_input("nx", 1)
    with col8:
        ny = st.number_input("ny", 1)
    with col9:
        nz = st.number_input("nz", 1)

    # 生成超胞
    if st.button("生成超胞"):
        st.session_state["supercell_atoms"] = bulk(element, crystal, a=a).repeat((nx, ny, nz))

    if "supercell_atoms" in st.session_state:
        with st.expander("展示/收起超胞结构", expanded=True):
            render_structure_with_info(
                st.session_state["supercell_atoms"],
                title="生成的超胞结构",
                prefix="supercell"
            )
            st.subheader("导出结构")
            fmt = st.selectbox("选择导出格式", ["xyz", "cif", "vasp"], key="supercell_export_fmt")

            buf = StringIO()
            st.session_state["supercell_atoms"].write(buf, format=fmt)

            st.download_button(
            "下载文件",
            buf.getvalue(),
            file_name=f"supercell_output.{fmt}",
            mime="text/plain",
            key="supercell_export_btn"
            )