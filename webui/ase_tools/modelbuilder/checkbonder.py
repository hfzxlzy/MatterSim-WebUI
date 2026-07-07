# 调用 numpy 库进行数值计算
import numpy as np
# 调用 ase.neighborlist 库邻接原子信息
from ase.neighborlist import PrimitiveNeighborList
# 调用 ase.data 库获取各元素共价半径
from ase.data import covalent_radii
# 调用 pymatgen 库进行化学键判断，BVAnalyzer 用于判断氧化态，CrystalNN 用于更准确的邻居判断
from pymatgen.core import Structure
from pymatgen.analysis.bond_valence import BVAnalyzer
from pymatgen.analysis.local_env import CrystalNN

# Pauling 电负性表（）
ELECTRONEGATIVITY = {
    # 1st period
    "H": 2.20, "He": 0.00,
    # 2nd period
    "Li": 0.98, "Be": 1.57, "B": 2.04, "C": 2.55, "N": 3.04, "O": 3.44, "F": 3.98, "Ne": 0.00,
    # 3rd period
    "Na": 0.93, "Mg": 1.31, "Al": 1.61, "Si": 1.98, "P": 2.19, "S": 2.58, "Cl": 3.16, "Ar": 0.00,
    # 4th period
    "K": 0.82, "Ca": 1.00, "Sc": 1.36, "Ti": 1.54, "V": 1.63, "Cr": 1.66, "Mn": 1.55,
    "Fe": 1.83, "Co": 1.88, "Ni": 1.92, "Cu": 1.90, "Zn": 1.65,
    "Ga": 1.81, "Ge": 2.01, "As": 2.18, "Se": 2.55, "Br": 2.96, "Kr": 3.00,
    # 5th period
    "Rb": 0.82, "Sr": 0.95, "Y": 1.22, "Zr": 1.33, "Nb": 1.59, "Mo": 2.16, "Tc": 1.91,
    "Ru": 2.20, "Rh": 2.28, "Pd": 2.20, "Ag": 1.93, "Cd": 1.69,
    "In": 1.78, "Sn": 1.96, "Sb": 2.05, "Te": 2.12, "I": 2.66, "Xe": 2.60,
    # 6th period
    "Cs": 0.79, "Ba": 0.89,
    "La": 1.11, "Ce": 1.12, "Pr": 1.13, "Nd": 1.14, "Pm": 1.13, "Sm": 1.17,
    "Eu": 1.19, "Gd": 1.21, "Tb": 1.13, "Dy": 1.22, "Ho": 1.23, "Er": 1.24,
    "Tm": 1.25, "Yb": 1.26, "Lu": 1.27,
    "Hf": 1.32, "Ta": 1.51, "W": 2.36, "Re": 1.93, "Os": 2.18, "Ir": 2.20,
    "Pt": 2.28, "Au": 2.54, "Hg": 2.00,
    "Tl": 1.62, "Pb": 1.87, "Bi": 2.02, "Po": 1.99, "At": 2.22, "Rn": 2.43,
    # 7th period（部分元素无可靠电负性，设为 0）
    "Fr": 0.79, "Ra": 0.92,
    "Ac": 1.09, "Th": 1.32, "Pa": 1.54, "U": 1.38, "Np": 1.36, "Pu": 1.28,
    "Am": 1.13, "Cm": 1.28, "Bk": 1.35, "Cf": 1.29, "Es": 1.31, "Fm": 1.34,
    "Md": 1.33, "No": 1.36, "Lr": 1.34,
}

# 判断单个跨胞键是否真实
def is_real_cross_cell_bond(pos, cell, i, j, offset, tol=2.5):
    offset = np.array(offset)
    # 最近 image 距离
    rij_pbc = pos[j] + offset @ cell - pos[i]
    dist_pbc = np.linalg.norm(rij_pbc)
    # 非 PBC 距离
    rij_no_pbc = pos[j] - pos[i]
    dist_no_pbc = np.linalg.norm(rij_no_pbc)
    # 非 PBC 距离接近 → 真实跨胞键
    return dist_no_pbc < dist_pbc * tol
# 判断整个结构是否是分子
def is_molecule_from_neighbors(pos, cell, I, J, S):
    for i, j, s in zip(I, J, S):
        if np.all(s == 0):
            continue
        if is_real_cross_cell_bond(pos, cell, i, j, s):
            return False  # 有真实跨胞键 → 晶体
    return True  # 所有跨胞键都是 image → 分子

# 化学键判断函数（ASE结构，容差，扩张，是否使用 CrystalNN）
def get_bonds(atoms, dr=1.15, cf=1.5, use_crystalnn=True):

    # -----------------------------
    # 1. 构建 pymatgen 结构对象
    # -----------------------------
    struct = Structure(
        lattice=atoms.cell.array,    # 晶胞
        species=atoms.get_chemical_symbols(),    # 元素符号列表
        coords=atoms.get_positions(),    # 原子坐标
        coords_are_cartesian=True    # 坐标是笛卡尔坐标
    )
    # 尝试获取氧化态信息（通过 BVAnalyzer ，以过滤同价态离子之间的错误键）
    try:
        # 获取装饰了氧化态信息的结构对象
        struct_oxi = BVAnalyzer().get_oxi_state_decorated_structure(struct)
        # 提取每个原子的氧化态，存储在数组中
        oxi_states = np.array([site.specie.oxi_state for site in struct_oxi])
        #print("✓ BVAnalyzer 成功推断价态")
        # 返回 BVAnalyzer 成功标记
        bv_success = True
    # 如果 BVAnalyzer 失败（例如对于某些复杂结构），则退回到无价态模式（金属、非金属单质、部分复杂硅酸盐）
    except Exception:
        # 直接使用原结构，所有氧化态设为 0
        struct_oxi = struct
        # 创建一个全零的氧化态数组，长度与原子数相同
        oxi_states = np.zeros(len(struct), dtype=int)
        #print("✗ BVAnalyzer 失败：使用无价态模式")
        # 返回 BVAnalyzer 失败标记
        bv_success = False

    # -----------------------------
    # 2. 可选：使用 CrystalNN 过滤邻居（矩阵化）
    # -----------------------------
    if use_crystalnn:
        # 如果不使用 CrystalNN，则创建 CrystalNN 对象
        cnn = CrystalNN()
        # 获取每个原子的 CrystalNN 邻居索引集合，存储在字典中
        cnn_neighbors = {
            i: {n["site_index"] for n in cnn.get_nn_info(struct_oxi, i)}
            for i in range(len(atoms))
        }
        # 获取原子总数 N
        N = len(atoms)
        # 创建一个 N×N 的布尔矩阵，初始值为 False
        cnn_matrix = np.zeros((N, N), dtype=bool)
        # 遍历 cnn_neighbors 字典，将邻居关系填充到 cnn_matrix 中
        for i, js in cnn_neighbors.items():
            cnn_matrix[i, list(js)] = True
    else:
        # 如果不使用 CrystalNN，则 cnn_matrix 设为 None，在后续过滤步骤中跳过
        cnn_matrix = None

    # -----------------------------
    # 3. ASE 邻域搜索，得到所有可能的键（矩阵化）
    # -----------------------------
    # 获取原子序数数组 Z
    Z = atoms.get_atomic_numbers()
    # 计算邻接列表的 cutoff 值，通常取共价半径之和乘以一个容差系数 cf
    cutoffs = covalent_radii[Z] * cf
    # 创建 PrimitiveNeighborList 对象，设置 cutoff 和 PBC 选项
    nl = PrimitiveNeighborList(
        cutoffs,    # cutoff 值
        self_interaction=False,    # 不考虑自环
        bothways=True,    # i-j 和 j-i 都记录
        skin=0.0    # 不使用额外的 skin
    )
    # 构建邻接列表，ASE 会自动考虑 PBC 和最近 image
    nl.update(atoms.pbc, atoms.get_cell(complete=True), atoms.positions)

    # -----------------------------
    # 4. 一次性展开所有邻居对，得到 I、J、S 三个数组
    # -----------------------------
    # neighbors 是一个列表，长度为原子数，每个元素是一个邻居索引列表
    neighbors = nl.neighbors
    # displacements 是一个列表，长度为原子数，每个元素是一个对应邻居的 PBC 偏移列表
    disps = nl.displacements
    # 通过重复原子索引和连接邻居索引，得到 I、J、S 三个数组
    counts = np.array([len(n) for n in neighbors])
    # I：原子 i 的索引
    I = np.repeat(np.arange(len(atoms)), counts)    # (M,1)
    # J：原子 j 的索引
    J = np.concatenate(neighbors)    # (M,1)
    # S：原子 j 相对于 i 的 PBC 偏移（整数向量）
    S = np.concatenate(disps)   # (M,3)

    # -----------------------------
    # 5. 计算原子间距离（矩阵化）
    # -----------------------------
    # 获取原子坐标和晶胞信息
    pos = atoms.get_positions()
    # 获取晶胞矩阵（3×3）
    cell = atoms.cell.array
    # 计算原子对 (i,j) 的最近 image 坐标
    rj_image = pos[J] + S @ cell
    # 计算原子 i 和 j_image 之间的距离
    rij = rj_image - pos[I]
    # 计算距离的欧几里得范数，得到一个长度为 M 的距离数组
    dist = np.linalg.norm(rij, axis=1)

    # -----------------------------
    # 6. 距离过滤
    # -----------------------------
    # 计算每对原子 i 和 j 的共价半径之和乘上容差 dr，得到一个长度为 M 的距离阈值数组
    R = (covalent_radii[Z][I] + covalent_radii[Z][J]) * dr
    # 创建一个布尔数组，表示哪些原子对满足距离条件
    mask = dist < R

    # -----------------------------
    # 7. 判断是否是分子（仅用于过滤逻辑，不影响 bonds 输出）
    # -----------------------------
    is_molecule = is_molecule_from_neighbors(pos, cell, I, J, S)

    # -----------------------------
    # 8. 价态过滤
    # -----------------------------
    # 获取原子 i 和 j 的氧化态
    oi = oxi_states[I]
    oj = oxi_states[J]
    # 若结构为分子则跳过价态筛选
    if is_molecule:
        #print("✗ 输入分子结构：不进行价态筛选")
        pass
    else:
        # 价态过滤条件：同号且非 0 的原子对不成键
        mask &= ~((oi != 0) & (oj != 0) & (oi * oj > 0))
        #print("✓ 输入晶体结构：进行价态筛选")

    # -----------------------------
    # 8. CNN 过滤（矩阵化）
    # -----------------------------
    # 如果使用 CrystalNN 过滤邻居，则检查 j 是否在 i 的 CrystalNN 邻居列表中
    if cnn_matrix is not None:
        mask &= cnn_matrix[I, J]

    # -----------------------------
    # 9. BVAnalyzer 失败时：推导原子电性（atom_charges）并剔除非键关系
    # -----------------------------
    # 获取元素符号
    symbols = atoms.get_chemical_symbols()
    if (not bv_success) or np.all(oxi_states == 0):
        # 获取邻接成键原子
        I_bond = I[mask]
        J_bond = J[mask]
        # 统计每个原子的邻居电负性总和
        atom_charges = np.zeros(len(atoms), dtype=float)    # 
        coord = np.bincount(I_bond, minlength=len(atoms))    # 原子 i 的成键邻居数
        sum_nn_en = np.zeros(len(atoms), dtype=float)    
        # 原子 i 所有邻居的电负性之和
        for ii, jj in zip(I_bond, J_bond):
            sum_nn_en[ii] += ELECTRONEGATIVITY[symbols[jj]]
        # 遍历相邻原子，计算“原子电性方向”
        for i in range(len(atoms)):
            if coord[i] > 0:
                # 计算邻居平均电负性AVGER(Xi)
                avg_nn = sum_nn_en[i] / coord[i]
                # 原子电性 = 邻居平均电负性 − 自身电负性
                atom_charges[i] = avg_nn - ELECTRONEGATIVITY[symbols[i]]
        # 电性离散化为 -1 / 0 / +1
        atom_charges = np.sign(atom_charges)
        # 若结构为分子则跳过价态筛选
        if is_molecule:
            #print("✗ 输入分子结构：不进行价态筛选")
            pass
        else:
            #print("✓ 输入晶体结构：进行价态筛选")
            # 电性辅助过滤成键
            for k in range(len(I)):
                if not mask[k]:
                    continue
                ii = I[k]
                jj = J[k]
                # 同号且非 0 电性不成键
                if atom_charges[ii] != 0 and atom_charges[ii] == atom_charges[jj]:
                    mask[k] = False           
    else:
        # BVAnalyzer 成功 → 不复制 oxi_states，不混用
        atom_charges = None

    # -----------------------------
    # 10. 输出 bonds
    # -----------------------------
    # 根据最终的 mask 过滤 I、J、S 三个数组，得到满足条件的化学键列表
    I = I[mask]
    J = J[mask]
    S = S[mask]
    # 构建 bonds 列表，每个元素是一个字典，包含原子 i、j 的索引和 PBC 偏移
    bonds = [
        {
            "i": int(i),    # 原子 i 的索引
            "j": int(j),    # 原子 j 的索引
            "offset": np.round(s).astype(int).tolist()    # PBC 偏移，转换为整数列表
        }
        # 遍历过滤后的原子对，构建 bonds 列表
        for i, j, s in zip(I, J, S)
    ]

    return bonds, oxi_states, atom_charges
    # 返回所有化学键的列表，每个键包含 i, j 和 offset 信息、化合价、原子电性
    # 例如：[{"i": i, "j": j, "offset": [la, lb, lc]}, ...]
    # 例如：[+4, +4, 0, -2, ...]
    # 例如：[+1, +1, 0, -1, ...]