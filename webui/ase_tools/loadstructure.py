# ASE 结构解析
# 调用h5py解析hdf文件
import h5py
# 调用nmpy库进行数值计算
import numpy as np
# 调用streamlit库构建结构查看界面
import streamlit as st
# 调用scipy子库进行矢量计算
from scipy.spatial import Voronoi
# 调用io库处理文件输入输出
from io import StringIO, BytesIO
# 调用ase库读取结构文件并进行处理
from ase import Atoms
from ase.io import read
from ase.io.formats import filetype

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

# 结构文件类型分析函数
def detect_fmt(uploaded):
    name = uploaded.name
    # 1. POSCAR/CONTCAR
    if name.upper() in ["POSCAR", "CONTCAR", "CENTCAR"]:
        return "vasp"
    # 2. QE .in
    if name.lower().endswith(".in"):
        return "qe-in"
    # 3. txt 当作 POSCAR
    if name.lower().endswith(".txt"):
        return "vasp"
    # 4. 让 ASE 自己判断扩展名
    try:
        return filetype(uploaded, read=False)
    except:
        return None

# 结构导入解析函数
def load_structure(uploaded):
    # -----------------------------
    # 解析结构文件（共享 atoms）
    # -----------------------------
    raw = uploaded.getvalue()
    fmt = detect_fmt(uploaded)

    # 尝试用文本方式解析，失败后用二进制方式解析（处理不同类型的文件上传）
    text = raw.decode("utf-8", errors="ignore")
    # 如果是 QE 结构片段 .in 文件 → 用自定义解析器
    if fmt == "qe-in":
        return  parse_qe_structure(text)
    else:
        try:
            return read(StringIO(text), format=fmt)
        except Exception:
            return read(BytesIO(raw), format=fmt)
        
# 从H5文件中获取声子演示相关信息
def load_structure_from_h5(path, labels_info):
    with h5py.File(path, "r") as h5:
        # === structure ===
        lattice = h5["structure/lattice"][:]
        scaled_positions = h5["structure/frac_coords"][:]
        symbols = [s.decode() for s in h5["structure/symbols"][:]]
        # === kpath ===
        labels = [l.decode() for l in h5["kpath/labels"][:]]
        segment_nq = h5["kpath/segment_nqpoint"][:]
        # === phonon qpoints ===
        qpoints = h5["phonon/qpoints"][:]  # 所有采样点
    # === 构造 ASE Atoms ===
    atoms = Atoms(
        symbols=symbols,
        cell=lattice,
        scaled_positions=scaled_positions,
        pbc=True
    )
    # === 计算倒格矢 ===
    r = np.linalg.inv(lattice).T    # 不带 2π 的倒格矢
    reciprocal_lattice = r.tolist()  # 转成 JSON 可序列化格式   
    # === 推导高对称点坐标（原始点序列） ===
    segment_start = np.cumsum([0] + list(segment_nq[:-1]))
    segment_end   = segment_start + np.array(segment_nq) - 1
    # 存储起点和终点索引
    start_indices = segment_start.tolist()
    end_indices   = segment_end.tolist()
   # === 按 labels_info 切分段（含断点标签） ===
    def get_start(lab):
        return lab.split("|")[1] if "|" in lab else lab
    def get_end(lab):
        return lab.split("|")[0] if "|" in lab else lab
    label_segments = []
    start_label = get_start(labels_info[0])
    for i in range(1, len(labels_info)):
        end_label = get_end(labels_info[i])
        label_segments.append((start_label, end_label))
        start_label = get_start(labels_info[i])
    # === 将 start_indices / end_indices 按顺序排入段坐标 ===
    highsym_points = []
    for i, (lab_s, lab_e) in enumerate(label_segments):
        s_idx = start_indices[i]
        e_idx = end_indices[i]
        # 起点
        highsym_points.append({
            "label": lab_s,
            "coords": qpoints[s_idx].tolist()
        })
        # 终点
        highsym_points.append({
            "label": lab_e,
            "coords": qpoints[e_idx].tolist()
        })
    # === 计算布里渊区顶点（Voronoi） ===
    b1, b2, b3 = r  # 三个倒格矢
    grid = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            for k in range(-1, 2):
                grid.append(i*b1 + j*b2 + k*b3)
    grid = np.array(grid)

    vor = Voronoi(grid)
    origin_index = np.argmin(np.linalg.norm(grid, axis=1))
    region = vor.regions[vor.point_region[origin_index]]
    bz_vertices = vor.vertices[region].tolist()
    #print(type(atoms))
    # 统一写成转成 JSON 可序列化格式 
    bz_json ={
        "highsym_points": highsym_points,
        "reciprocal_lattice": reciprocal_lattice,
        "bz_vertices": bz_vertices
    }
    # 返回 atoms + 高对称点 + 倒格矢 + 布里渊区断点
    return atoms, bz_json