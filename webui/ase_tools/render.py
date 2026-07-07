# ASE结构渲染模块
# 调用streamlit库构建结构渲染界面
import streamlit as st
# 调用io库中的StringIO类处理字符串输入输出，方便在Web界面上显示结构信息
from io import StringIO
# 调用normalatoms模块中的normalize_atoms函数，将ASE Atoms对象转换为统一的JSON数据结构，便于前端渲染
from webui.ase_tools.modelbuilder.normalatoms import normalize_atoms
# 调用3jstrans模块中的Cell_renderer_html函数，生成Three.js渲染器的HTML代码，用于在Streamlit中显示晶胞3D结构
from webui.ase_tools.modelbuilder.trijstransCell import Cell_renderer_html
# 调用3jstrans模块中的Brillouin_renderer_html函数，生成Three.js渲染器的HTML代码，用于在Streamlit中显示布里渊区3D结构
from webui.ase_tools.modelbuilder.trijstransBrillouin import Brillouin_renderer_html

# 结构渲染函数
def render_structure_with_info(
        mode="cell",    # 渲染器调用模式(cell/bz)
        atoms=None,    # 结构数据(默认为空)
        phonon=None,    # 声子数据(默认为空)
        Bz=None,    # 布里渊区数据(默认为空)
        TJSmode="auto",    # 3JS调用模式(auto/local/cdn)
        height=750,    # 容器高度(NUMpx)
        width="stretch"    # 容器宽度(NUMpx/NUM%/"stretch")
    ):

    # 1. 结构归一化：将 ASE Atoms 对象转换为统一 JSON 数据结构
    json_data = None
    if mode == "cell":
        json_data = normalize_atoms(atoms)

    # 2.转译生成html用于模型显示及交互
    if mode == "cell":
        three_html = Cell_renderer_html(
            rawdata=json_data,    #结构数据
            phonondata=phonon,    #声子数据
            mode=TJSmode,    # auto/local/cdn
            threejs_local="/app/static/3jsmain/three.module.js",    # local_path
            addons_local="/app/static/3addons/",    # local_path
            threejs_url="https://cdn.jsdelivr.net/npm/three@v0.185.0/build/three.module.js",    # cdn_url
            addons_url="https://cdn.jsdelivr.net/npm/three@v0.185.0/examples/jsm/",    # cdn_url
        )
    elif mode == "bz":
        three_html = Brillouin_renderer_html(
            Bz=Bz,    #结构数据
            mode=TJSmode,    # auto/local/cdn
            threejs_local="/app/static/3jsmain/three.module.js",    # local_path
            addons_local="/app/static/3addons/",    # local_path
            threejs_url="https://cdn.jsdelivr.net/npm/three@v0.185.0/build/three.module.js",    # cdn_url
            addons_url="https://cdn.jsdelivr.net/npm/three@v0.185.0/examples/jsm/",    # cdn_url
        )

    # 3.使用 Streamlit 的 st.iframe 方法渲染完整的HTML内容，并允许其中的JavaScript（用于3Dmol渲染）执行
    st.iframe(src=three_html, height=height, width=width)
    # 打印生成的HTML文件内容
    #print(three_html)
    # 4.下载按钮
    if atoms is not None:
        fname = f"{atoms.get_chemical_formula()}_structureviewer.html"
    else:
        fname = "BrillouinZone_viewer.html"
    st.download_button(
        label="下载 HTML（Three.js 渲染器）",
        data=three_html,
        file_name=fname,
        mime="text/html"
    )