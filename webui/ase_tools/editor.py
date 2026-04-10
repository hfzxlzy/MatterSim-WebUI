# ASE结构编辑组件
# 调用streamlit库构建结构构建界面
import streamlit as st
# 调用pandas库处理结构数据表格
import pandas as pd
# 调用io库处理文件输入输出
from io import StringIO, BytesIO
# 调用ase库读取结构文件并进行处理
from ase import Atoms, Atom
from ase.io import read
#调用render模块中的函数渲染结构和相关信息
from webui.ase_tools.render import render_structure_with_info

# 结构编辑组件
def show_structure_editor():
    st.header("结构编辑")

    uploaded = st.file_uploader("上传结构文件进行编辑", type=["xyz", "cif", "vasp", "txt"])

    if not uploaded:
        st.info("请先上传结构文件")
        return

    raw = uploaded.getvalue()
    filename = uploaded.name.lower()

    if filename.endswith(".xyz"):
        fmt = "xyz"
    elif filename.endswith(".cif"):
        fmt = "cif"
    else:
        fmt = "vasp"

    try:
        text = raw.decode("utf-8")
        atoms = read(StringIO(text), format=fmt)
    except UnicodeDecodeError:
        atoms = read(BytesIO(raw), format=fmt)

    # -----------------------------
    # 1. 构建可编辑 DataFrame（带复选框）
    # -----------------------------
    df = pd.DataFrame({
        "选中": [False] * len(atoms),
        "元素": atoms.get_chemical_symbols(),
        "x": atoms.positions[:, 0],
        "y": atoms.positions[:, 1],
        "z": atoms.positions[:, 2],
    })

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=False,
        key="atom_editor"
    )

    # -----------------------------
    # 2. 将 DataFrame 写回 atoms
    # -----------------------------
    new_atoms = []

    for i in range(len(edited_df)):
        sym = edited_df.loc[i, "元素"]
        x = edited_df.loc[i, "x"]
        y = edited_df.loc[i, "y"]
        z = edited_df.loc[i, "z"]
        new_atoms.append(Atom(sym, (x, y, z)))

    atoms = Atoms(new_atoms)

    # -----------------------------
    # 3. 自动高亮最后一个勾选的行
    # -----------------------------
    checked_rows = edited_df.index[edited_df["选中"] == True].tolist()
    #highlight_id = checked_rows[-1] if checked_rows else None

    # -----------------------------
    # 4. 使用统一的 3D 渲染组件（只渲染一次）
    # -----------------------------
    render_structure_with_info(
        atoms, title="编辑后的结构",
        prefix="editor",
        highlight_ids=checked_rows
    )

    # -----------------------------
    # 5. 导出编辑后的结构
    # -----------------------------
    st.subheader("导出编辑后的结构")
    fmt = st.selectbox("选择导出格式", ["xyz", "cif", "vasp"], key="editor_export_fmt")

    buf = StringIO()
    atoms.write(buf, format=fmt)

    st.download_button(
    "下载文件",
    buf.getvalue(),
    file_name=f"edited_output.{fmt}",
    mime="text/plain",
    key="editor_export_btn"
    )
