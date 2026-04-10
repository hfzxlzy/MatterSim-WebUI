# ASE结构查看组件
# 调用streamlit库构建结构查看界面
import streamlit as st
# 调用io库处理文件输入输出
from io import StringIO, BytesIO
# 调用ase库读取结构文件并进行处理
from ase.io import read
#调用render模块中的函数渲染结构和相关信息
from webui.ase_tools.render import render_structure_with_info

# 结构查看组件
def show_structure_viewer_page():
    st.header("结构查看")

    # 上传文件（整个页面共享）
    uploaded = st.file_uploader(
        "上传结构文件 (.xyz / .cif / POSCAR)",
        type=["xyz", "cif", "vasp", "txt", "traj"],
        key="viewer_upload"
    )

    if not uploaded:
        st.info("请先上传结构文件")
        return

    # -----------------------------
    # 解析结构文件（共享 atoms）
    # -----------------------------
    raw = uploaded.getvalue()
    filename = uploaded.name.lower()

    if filename.endswith(".xyz"):
        fmt = "xyz"
    elif filename.endswith(".cif"):
        fmt = "cif"
    elif filename.endswith(".traj"):
        fmt = "traj"
    else:
        fmt = "vasp"

    try:
        text = raw.decode("utf-8")
        atoms = read(StringIO(text), format=fmt)
    except UnicodeDecodeError:
        atoms = read(BytesIO(raw), format=fmt)

    # -----------------------------
    # 顶部固定渲染（不会随 tab 切换而重建）
    # -----------------------------
    st.subheader("结构预览（固定显示）")
    render_structure_with_info(atoms, title="结构查看", prefix="viewer")

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
        
    # 超胞预览（放在查看结构的 tab 中）
    with st.expander("展开/关闭超胞预览", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            na = st.number_input("a 方向倍数", 1, 10, 1, key="viewer_na")
        with col2:
            nb = st.number_input("b 方向倍数", 1, 10, 1, key="viewer_nb")
        with col3:
            nc = st.number_input("c 方向倍数", 1, 10, 1, key="viewer_nc")

        if st.button("生成超胞", key="viewer_supercell_btn"):
            supercell = atoms * (int(na), int(nb), int(nc))
            st.success(f"已生成超胞：{len(supercell)} 个原子")

            # 渲染超胞
            render_structure_with_info(
                supercell,
                title="导入结构的超胞",
                prefix="viewer_supercell"
            )

            # 导出结构文件
            fmt_out2 = st.selectbox(
                "导出超胞格式",
                ["xyz", "cif", "vasp"],
                key="viewer_supercell_fmt"
            )

            if st.button("下载超胞文件", key="viewer_supercell_download_btn"):
                if fmt_out2 == "cif":
                    # cif 格式需要特殊处理，写入字符串后再下载
                    buf2 = BytesIO()
                    supercell.write(buf2, format="cif")
                    data = buf2.getvalue()
                else:
                    buf2 = StringIO()
                    supercell.write(buf2, format=fmt_out2)
                    data = buf2.getvalue()
                st.download_button(
                    "下载超胞文件",
                    data,
                    file_name=f"supercell.{fmt_out2}",
                    mime="text/plain",
                    key="viewer_supercell_download"
                )

    # Tab 2：格式转换
    with tab_convert:
        st.subheader("格式转换")

        fmt_out = st.selectbox(
            "选择输出格式",
            ["xyz", "cif", "vasp"],
            key="viewer_fmt_out"
        )

        if st.button("转换并下载", key="viewer_convert_btn"):
            if fmt_out == "cif":
                # cif 格式需要特殊处理，写入字符串后再下载
                buf = BytesIO()
                atoms.write(buf, format="cif")
                data = buf.getvalue()
            else:
                buf = StringIO()
                atoms.write(buf, format=fmt_out)
                data = buf.getvalue()
            st.download_button(
                "下载文件",
                data,
                file_name=f"output.{fmt_out}",
                mime="text/plain",
                key="viewer_download"
            )