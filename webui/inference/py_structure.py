# 结构输入相关模块
# 调用streamlit库
import streamlit as st
# 调用ase库
import ase
# 调用ase库,用于结构输入和处理
from ase.io import read, write
from ase import Atoms
from ase.build import bulk
# 调用numpy库,用于数据处理
import numpy as np
# 调用io库,用于文件处理
from io import StringIO, BytesIO

#通用对象结构片段生成函数
def generate_structure_input(state):
    #通用结构输入片段：
    #Predict: m × n
    #Relax:   m × 1
    #Phonon:  1 × 1
    mode = state.structure_mode
    files = state.file_list
    
    # 结构预测：允许 m×n
    if mode == "mxn":
        repeat_n = state.repeat_n
        return f"""
# 输入结构文件列表（m 个）
files = {files}

# 每个结构重复次数 n
repeat_n = {repeat_n}

structures = []
for f in files:
    atoms = read(f)
    structures.extend([atoms] * repeat_n)

print(f"Loaded {{len(files)}} structures, each repeated {{repeat_n}} times")
print(f"Total batch size: {{len(structures)}}")
"""

    # 松弛：强制 m×1
    elif mode == "mx1":
        return f"""
# 输入结构文件列表（m 个）
files = {files}

# 松弛不支持重复结构，强制 mx1
structures = [read(f) for f in files]

print(f"Loaded {{len(structures)}} structures for relaxation")
"""

    # 声子：强制 1×1
    elif mode == "1x1":
        return f"""
# 声子计算仅支持单结构
file = {files}[0]
atoms = read(file)

print("Loaded structure for phonon calculation:", file)
"""

    else:
        return "# 未知模式"

#结构输入函数
def structure_input_block(key_prefix=""):
    st.markdown("### 结构输入")

    # 选择输入方式
    mode = st.radio(
        "选择结构来源",
        ["上传结构文件", "输入AES结构码"],
        key=f"{key_prefix}_struct_mode",
    )

    file_list = []

    # --- 上传结构文件UI（支持多个） ---
    if mode == "上传结构文件":
        uploaded_files = st.file_uploader(
            "上传结构文件 (.xyz/.cif/POSCAR)，可多选",
            type=["xyz", "cif", "vasp", "txt"],
            accept_multiple_files=True,
            key=f"{key_prefix}_upload",
        )

        if uploaded_files:
            for uploaded in uploaded_files:
                raw = uploaded.getvalue()
                filename = uploaded.name.lower()

                # 自动识别格式
                if filename.endswith(".xyz"):
                    fmt = "xyz"
                elif filename.endswith(".cif"):
                    fmt = "cif"
                else:
                    fmt = "vasp"

                # 读取结构
                try:
                    text = raw.decode("utf-8")
                    atoms = read(StringIO(text), format=fmt)
                except UnicodeDecodeError:
                    atoms = read(BytesIO(raw), format=fmt)

                # 写入临时文件
                tmp_path = f"/tmp/{filename}"
                write(tmp_path, atoms)
                file_list.append(tmp_path)

            st.success(f"已加载 {len(file_list)} 个结构文件")
            st.session_state.file_list = file_list

    # --- 手写 ASE 结构代码 ---
    else:
        st.info("请输入 Python 代码，并确保定义变量 atoms，例如：\natoms = bulk('Si', 'diamond', a=5.43)")

        code = st.text_area(
            "输入 ASE 结构码",
            value='atoms = bulk("Si", "diamond", a=5.43)',
            height=200,
            key=f"{key_prefix}_manual_code"
        )

        if st.button("执行代码生成结构", key=f"{key_prefix}_run_code"):
            try:
                local_env = {
                    "ase": ase,
                    "Atoms": Atoms,
                    "bulk": bulk,
                    "read": read,
                    "np": np,
                }

                exec(code, {}, local_env)

                if "atoms" not in local_env:
                    st.error("代码未定义变量 atoms")
                else:
                    atoms = local_env["atoms"]
                    if not isinstance(atoms, Atoms):
                        st.error("变量 atoms 不是 ASE Atoms 对象")
                    else:
                        tmp_path = "/tmp/webui_manual_structure.xyz"
                        write(tmp_path, atoms, format="xyz")

                        st.session_state.file_list = [tmp_path]

                        st.success("结构生成成功")

            except Exception as e:
                st.error(f"执行失败：{e}")

    return st.session_state.get("file_list", [])
