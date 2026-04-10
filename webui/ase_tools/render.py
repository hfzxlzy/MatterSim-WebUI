# ASE结构渲染模块
# 调用streamlit库构建结构渲染界面
import streamlit as st
# 调用py3Dmol库进行3D结构渲染
import py3Dmol
# 调用io库中的StringIO类处理字符串输入输出，方便在Web界面上显示结构信息
from io import StringIO

# 结构渲染函数
def render_structure_with_info(
        atoms,
        title="结构预览",
        prefix="info",
        highlight_ids=None,
        rotation_override=None
    ):

    # -----------------------------
    # 自动识别元素 + 颜色表
    # -----------------------------
    jmol_colors = {
        "H": "#FFFFFF", "He": "#D9FFFF",
        "Li": "#CC80FF", "Be": "#C2FF00", "B": "#FFB5B5", "C": "#909090",
        "N": "#3050F8", "O": "#FF0D0D", "F": "#90E050", "Ne": "#B3E3F5",

        "Na": "#AB5CF2", "Mg": "#8AFF00", "Al": "#BFA6A6", "Si": "#F0C8A0",
        "P": "#FF8000", "S": "#FFFF30", "Cl": "#1FF01F", "Ar": "#80D1E3",

        "K": "#8F40D4", "Ca": "#3DFF00", "Sc": "#E6E6E6", "Ti": "#BFC2C7",
        "V": "#A6A6AB", "Cr": "#8A99C7", "Mn": "#9C7AC7", "Fe": "#E06633",
        "Co": "#F090A0", "Ni": "#50D050", "Cu": "#C88033", "Zn": "#7D80B0",
        "Ga": "#C28F8F", "Ge": "#668F8F", "As": "#BD80E3", "Se": "#FFA100",
        "Br": "#A62929", "Kr": "#5CB8D1",

        "Rb": "#702EB0", "Sr": "#00FF00", "Y": "#94FFFF", "Zr": "#94E0E0",
        "Nb": "#73C2C9", "Mo": "#54B5B5", "Tc": "#3B9E9E", "Ru": "#248F8F",
        "Rh": "#0A7D8C", "Pd": "#006985", "Ag": "#C0C0C0", "Cd": "#FFD98F",
        "In": "#A67573", "Sn": "#668080", "Sb": "#9E63B5", "Te": "#D47A00",
        "I": "#940094", "Xe": "#429EB0",

        "Cs": "#57178F", "Ba": "#00C900", "La": "#70D4FF", "Ce": "#FFFFC7",
        "Pr": "#D9FFC7", "Nd": "#C7FFC7", "Pm": "#A3FFC7", "Sm": "#8FFFC7",
        "Eu": "#61FFC7", "Gd": "#45FFC7", "Tb": "#30FFC7", "Dy": "#1FFFC7",
        "Ho": "#00FF9C", "Er": "#00E675", "Tm": "#00D452", "Yb": "#00BF38",
        "Lu": "#00AB24",

        "Hf": "#4DC2FF", "Ta": "#4DA6FF", "W": "#2194D6", "Re": "#267DAB",
        "Os": "#266696", "Ir": "#175487", "Pt": "#D0D0E0", "Au": "#FFD123",
        "Hg": "#B8B8D0", "Tl": "#A6544D", "Pb": "#575961", "Bi": "#9E4FB5",
        "Po": "#AB5C00", "At": "#754F45", "Rn": "#428296",

        "Fr": "#420066", "Ra": "#007D00", "Ac": "#70ABFA", "Th": "#00BAFF",
        "Pa": "#00A1FF", "U": "#008FFF", "Np": "#0080FF", "Pu": "#006BFF",
        "Am": "#545CF2", "Cm": "#785CE3", "Bk": "#8A4FE3", "Cf": "#A136D4",
        "Es": "#B31FD4", "Fm": "#B31FBA", "Md": "#B30DA6", "No": "#BD0D87",
        "Lr": "#C70066"
    }
    symbols = sorted(set(atoms.get_chemical_symbols()))

    # -----------------------------
    # 渲染模式、晶胞框、测量工具
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    max_idx = len(atoms) - 1
    default_a = 0
    default_b = 1 if max_idx >= 1 else max_idx
    default_c = 2 if max_idx >= 2 else max_idx

    with col1:
        #切换主题
        theme = st.radio(
            "背景主题",
            ["浅色", "深色"],
            horizontal=True,
            key=f"{prefix}_theme"
        )
        st.subheader("测量工具")
        atom_a = st.number_input(
            "原子 A",
            min_value=0,
            max_value=max_idx,
            value=default_a,
            key=f"{prefix}_atom_A"
        )
        
    with col2:
        #切换渲染模式
        render_mode = st.selectbox(
            "渲染模式",
            ["ball_and_stick", "stick", "ball"],
            key=f"{prefix}_render_mode"
        )
        st.subheader("  ")
        atom_b = st.number_input(
            "原子 B",
            min_value=0,
            max_value=max_idx,
            value=default_b,
            key=f"{prefix}_atom_b"
        )
    with col3:
        show_cell_raw = st.radio(
            "晶胞框状态（unit cell）",
            ["显示", "隐藏"],
            horizontal=True,
            key=f"{prefix}_show_cell"
        )
        st.subheader("  ")
        atom_c = st.number_input(
            "原子 C（用于键角）",
            min_value=0,
            max_value=max_idx,
            value=default_c,
            key=f"{prefix}_atom_C"
        )
    #布尔值转换
    show_cell = (show_cell_raw == "显示")
    dist = atoms.get_distance(atom_a, atom_b)
    angle = None
    if len(atoms) >= 3 and atom_a != atom_b and atom_b != atom_c and atom_a != atom_c:
        try:
            angle = atoms.get_angle(atom_a, atom_b, atom_c)
        except ZeroDivisionError:
            angle = None

    # -----------------------------
    # 输出测量结果（保持原样）
    # -----------------------------
    with col1:
        st.markdown(f"**键长 A-B：** {dist:.3f} Å")
    with col2:
        if angle is None:
            st.markdown(f"**键角 A-B-C：** N/A ")
        else:
            st.markdown(f"**键角 A-B-C：** {angle:.2f}°")
    with col3:
        st.markdown("  ")

    # -----------------------------
    # 主题颜色
    # -----------------------------
    if theme == "浅色":
        bg_color = "#f8f9fa"
        border_color = "#4A90E2"
        text_color = "#000"
    else:
        bg_color = "#1e1e1e"
        border_color = "#666"
        text_color = "#fff"

    # -----------------------------
    # 结构信息（保持原样）
    # -----------------------------
    formula = atoms.get_chemical_formula()
    natoms = len(atoms)

    cell = atoms.get_cell()
    if cell is not None and cell.rank == 2:
        a, b, c = cell.lengths()
        alpha, beta, gamma = cell.angles()
    else:
        a = b = c = alpha = beta = gamma = None
    # -----------------------------
    # 生成 xyz
    # -----------------------------
    buf = StringIO()
    atoms.write(buf, format="xyz")
    xyz_str = buf.getvalue()

    # -----------------------------
    # 高亮元素选项
    # -----------------------------
    highlight_elem = st.radio(
        "高亮元素",
        ["无"] + symbols,
        horizontal=True,
        key=f"{prefix}_highlight"
    )
    # -----------------------------
    # 旋转滑条（主渲染框使用）
    # -----------------------------
    colx, coly, colz = st.columns(3)

    with colx:
        rx = st.slider("绕 X 轴旋转", 0, 360, 0, key=f"{prefix}_rx")
    with coly:
        ry = st.slider("绕 Y 轴旋转", 0, 360, 0, key=f"{prefix}_ry")
    with colz: 
        rz = st.slider("绕 Z 轴旋转", 0, 360, 0, key=f"{prefix}_rz")

    # -----------------------------
    # 渲染 py3Dmol
    # -----------------------------
    view = py3Dmol.view(width=600, height=450)
    view.addModel(xyz_str, "xyz")

    if render_mode == "stick":
        view.setStyle({"stick": {}})
    elif render_mode == "ball":
        view.setStyle({"sphere": {"scale": 0.3}})
    else:
        view.setStyle({"stick": {}, "sphere": {"scale": 0.3}})

    if show_cell:
        view.addUnitCell()
    #高亮选中原子
    if highlight_ids:
        for idx in highlight_ids:
            view.setStyle(
                {"serial": idx + 1},
                {"sphere": {"color": "#FFFF00", "radius": 0.5}}
            )
    #否则按元素高亮
    elif highlight_elem != "无":
        color = jmol_colors.get(highlight_elem, "#FF0000")
        view.setStyle(
            {"elem": highlight_elem},
            {"sphere": {"color": color, "radius": 0.5}}
        )

    # 应用旋转
    view.rotate(rx, "x")
    view.rotate(ry, "y")
    view.rotate(rz, "z")

    view.zoomTo()

    # -----------------------------
    # 右侧颜色图例（保持原样）
    # -----------------------------
    legend_html = "<div style='padding-left:20px;'>"
    legend_html += "<div style='font-size:16px;font-weight:bold;margin-bottom:8px;'>原子颜色图例</div>"

    for sym in symbols:
        color = jmol_colors.get(sym, "#BBBBBB")
        legend_html += f"""
        <div style="display:flex;align-items:center;margin-bottom:6px;">
            <div style="width:16px;height:16px;background:{color};border-radius:50%;margin-right:8px;"></div>
            <span style="font-size:14px;">{sym}</span>
        </div>
        """

    legend_html += "</div>"

    # -----------------------------
    # 卡片顶部（保持原样）
    # -----------------------------
    html_top = f"""
    <div style="
        border: 2px solid {border_color};
        border-radius: 10px;
        padding: 12px;
        background-color: {bg_color};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        color: {text_color};
        font-family: Arial, sans-serif;
    ">
        <div style="font-size: 20px; font-weight: bold; margin-bottom: 6px;">
            {title}
        </div>

        <div style="font-size: 14px; margin-bottom: 12px;">
            <b>化学式：</b> {formula}<br>
            <b>原子数：</b> {natoms}<br>
    """

    if a is not None:
        html_top += f"""
            <b>晶胞参数：</b><br>
            a = {a:.3f} Å, b = {b:.3f} Å, c = {c:.3f} Å<br>
            α = {alpha:.2f}°, β = {beta:.2f}°, γ = {gamma:.2f}°
        """

    html_top += """
        </div>

        <div style="display:flex;flex-direction:row;">
            <div style="flex:3;">
    """ + view._make_html() + """
            </div>

            <div style="flex:1;margin-left:20px;">
                """ + legend_html + """
            </div>
        </div>
    </div>
    """

    st.components.v1.html(html_top, height=650)