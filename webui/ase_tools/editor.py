# ASE结构编辑组件
# 调用streamlit库构建结构构建界面
import streamlit as st
# 调用pandas库处理结构数据表格
import pandas as pd
# 调用nmpy库进行数值计算
import numpy as np
# 调用io库处理文件输入输出
from io import StringIO, BytesIO
# 调用ase库读取结构文件并进行处理
from ase import Atoms, Atom
from ase.io import read
#调用render模块中的函数渲染结构和相关信息
from webui.ase_tools.render import render_structure_with_info

# QE输入文件解析函数
def parse_qe_structure(text):
    # 解析 QE 输入文件中的结构信息，返回 ASE Atoms 对象
    lines = text.splitlines()
    # 解析 ATOMIC_SPECIES、ATOMIC_POSITIONS 和 CELL_PARAMETERS
    species = []
    positions = []
    cell = []

    mode = None
    # 解析文件内容
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 识别不同部分的开始
        if line.startswith("ATOMIC_SPECIES"):
            mode = "species"
            continue
        if line.startswith("ATOMIC_POSITIONS"):
            mode = "positions"
            continue
        if line.startswith("CELL_PARAMETERS"):
            mode = "cell"
            continue
        # 解析不同部分的内容
        if mode == "species":
            parts = line.split()
            species.append(parts[0])
        # 解析原子位置和元素符号
        elif mode == "positions":
            parts = line.split()
            positions.append([parts[0], float(parts[1]), float(parts[2]), float(parts[3])])
        # 解析晶胞参数
        elif mode == "cell":
            parts = line.split()
            cell.append([float(x) for x in parts])

    # 构造 ASE Atoms
    symbols = [p[0] for p in positions]
    coords = np.array([p[1:] for p in positions], dtype=float)

    atoms = Atoms(symbols=symbols, scaled_positions=coords, cell=cell, pbc=True)
    return atoms

# 结构编辑组件
def show_structure_editor():
    st.header("结构编辑")

    uploaded = st.file_uploader("上传结构文件进行编辑", type=["xyz", "cif", "vasp", "txt", "in", "POSCAR"])

    if not uploaded:
        st.info("请先上传结构文件")
        return

    raw = uploaded.getvalue()
    filename = uploaded.name.lower()

    if filename.endswith(".xyz"):
        fmt = "xyz"
    elif filename.endswith(".cif"):
        fmt = "cif"
    elif filename.endswith(".in"):
        fmt = "qe-structure"
    else:
        fmt = "vasp"
    # 尝试用文本方式解析，失败后用二进制方式解析（处理不同类型的文件上传）
    text = raw.decode("utf-8", errors="ignore")
    # 如果是 QE 结构片段 .in 文件 → 用自定义解析器
    if filename.endswith(".in"):
        atoms = parse_qe_structure(text)
    else:
        try:
            atoms = read(StringIO(text), format=fmt)
        except Exception:
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
