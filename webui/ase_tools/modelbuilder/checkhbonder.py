import numpy as np
from ase.neighborlist import neighbor_list

# 氢键供体元素
HBOND_DONORS = {"O", "N", "F"}
# 氢键受体元素
HBOND_ACCEPTORS = {"O", "N", "F"}

def detect_hydrogen_bonds(atoms, max_dist=3.0, min_angle=120):
    """
    返回氢键列表：[(H_index, A_index, image_vector)]
    """

    positions = atoms.get_positions()
    symbols = atoms.get_chemical_symbols()
    cell = atoms.cell.array

    # 找到所有 H 原子
    H_indices = [i for i, s in enumerate(symbols) if s == "H"]

    # ASE 邻域搜索（找 H 附近的所有原子）
    i_list, j_list, S_list = neighbor_list("ijS", atoms, cutoff=max_dist)

    hbonds = []

    for i, j, S in zip(i_list, j_list, S_list):
        if i not in H_indices:
            continue

        H = i
        A = j
        A_symbol = symbols[A]

        # A 必须是受体
        if A_symbol not in HBOND_ACCEPTORS:
            continue

        # 找 H 的供体 D（必须是 O/N/F）
        # 找到与 H 成键的最近邻
        # 这里用简单距离判断（H–D 共价键 ~1 Å）
        H_pos = positions[H]
        D = None
        for k, pos in enumerate(positions):
            if symbols[k] in HBOND_DONORS:
                if np.linalg.norm(pos - H_pos) < 1.2:  # H–D 共价键
                    D = k
                    break
        if D is None:
            continue

        # 判断角度 D–H···A
        D_pos = positions[D]
        A_pos = positions[A] + S  # 加上 PBC 偏移

        v1 = D_pos - H_pos
        v2 = A_pos - H_pos

        angle = np.degrees(
            np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        )

        if angle < min_angle:
            continue

        # 计算 image vector
        image = np.round(np.linalg.solve(cell.T, S)).astype(int)

        hbonds.append((H, A, tuple(image)))

    return hbonds
