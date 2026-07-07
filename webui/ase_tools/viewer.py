# ASE结构查看组件
# 调用streamlit库构建结构查看界面
import streamlit as st
# 调用ase.io输出指定格式
from ase.io import write
# 调用io库处理文件输入输出
from io import StringIO, BytesIO
#调用render模块中的函数渲染结构和相关信息
from webui.ase_tools.render import render_structure_with_info
from webui.ase_tools.loadstructure import load_structure

# 结构查看组件
def show_structure_viewer_page():
    st.header("结构查看")

    # 上传文件（整个页面共享）
    uploaded = st.file_uploader(
        "上传结构文件 (.xyz / .cif / POSCAR/ .in)",
        type=["xyz", "cif", "vasp", "txt", "traj", "in", "POSCAR"],
        key="viewer_upload"
    )

    if not uploaded:
        st.info("请先上传结构文件")
        return

    # -----------------------------
    # 解析结构文件（共享 atoms）
    # -----------------------------
    try:
        # 尝试调用 load_structure 解析上传的文件
        atoms = load_structure(uploaded)
    except Exception as e:
        st.error(f"结构解析失败：{e}")
        return

    # -----------------------------
    # 顶部固定渲染（不会随 tab 切换而重建）
    # -----------------------------
    # 载入 html 渲染模块
    render_structure_with_info(mode="cell", atoms=atoms, TJSmode="auto")

    # -----------------------------
    # 下方两个 tab：查看结构 / 格式转换
    # -----------------------------
    tab_view, tab_convert = st.tabs(["查看结构", "格式转换"])

    # Tab 1：查看结构（可以放结构信息）
    with tab_view:
        st.subheader("结构信息")
        st.write(f"原子数：{len(atoms)}")
        st.write(f"化学式：{atoms.get_chemical_formula()}")

        st.markdown("---")
    
    # Tab 2：格式转换
    with tab_convert:
        st.subheader("格式转换")

        fmt_out_raw = st.selectbox(
            "选择输出格式",
            ["xyz", "cif", "vasp"],
            key="viewer_fmt_out"
        )
        # 统一格式名（去空格、转小写、把下划线改成短横线）
        fmt_out = fmt_out_raw.strip().lower().replace("_", "-")
        # 哪些格式需要二进制输出
        binary_formats = ["cif"]
        # 自动选择输出缓冲区类型
        if fmt_out in binary_formats:
            buf = BytesIO()
        else:
            buf = StringIO()
        # 写出结构
        write(buf, atoms, format=fmt_out)
        data = buf.getvalue()
        # 统一 MIME 类型（最稳妥）
        mime = "application/octet-stream"
        # 用户只需点击一次即可下载
        st.download_button(
            "转换并下载",
            data,
            file_name=f"output.{fmt_out}",
            mime=mime,
            key="viewer_download"
        )
