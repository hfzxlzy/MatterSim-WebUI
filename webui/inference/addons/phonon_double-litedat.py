import streamlit as st
from webui.inference.phonondraw import plot_phonon_interactive

# -----------------------------
# 声子计算脚本片段
# -----------------------------
def generate_phononDLD_block(state):
    return f"""
# 声子计算
atoms.calc = MatterSimCalculator(load_path=model_path,device=device)

ph = PhononWorkflow(
    atoms=atoms,
    find_prim={state.find_prim},
    work_dir="{state.phonon_work_dir}",
    amplitude={state.displacement},
    supercell_matrix=np.diag([{state.supercell}])
)

has_imag, phonons = ph.run()

# 简单声子谱绘制数据获取函数
def export_phonon_band(phonons, work_dir):   
    # phonopy 对象获取 K-path labels
    bs = phonons._band_structure
    labels_info = bs.labels    # 高对称点标签列表
    path_connections = bs._path_connections    # 从 path_connections 获取段间连续性
    # 从 phonopy 对象获取完整 band 结构
    band = phonons.get_band_structure_dict()
    dist_list = band["distances"]
    freq_list = band["frequencies"]
    # 拼接所有路径段的 distance
    distances = np.concatenate(dist_list)  # shape = (nqpoint,)
    # 拼接所有路径段的频率矩阵
    freqs = np.concatenate(freq_list, axis=0)  # shape = (nqpoint, 3N)
    # 拼成最终矩阵： (nqpoint, 1 + 3N)
    mat = np.hstack([distances.reshape(-1, 1), freqs])
    # 获取q点数和模式数
    nqpoint = mat.shape[0]
    nmodes = freqs.shape[1]
    # 1) 计算每段的起始 index，用来定位高对称点在 distance 里的位置
    # 从 distances 自动推断segment_nqpoint
    segment_nq = [len(seg) for seg in dist_list]          # e.g. [71,71,101,...]
    # 从0开始累加每段的 q 点数，得到每段的起始 index
    segment_start = [0]
    for n in segment_nq[:-1]:
        segment_start.append(segment_start[-1] + n)
    # 2) 计算每段的 distance 起止点
    # 定义段范围列表 segment_ranges，元素为 (d_start, d_end)，表示每段的 distance 起止点
    segment_ranges = []
    # 遍历每段，计算起止 distance，并保存到 segment_ranges
    for i, nseg in enumerate(segment_nq):
        i_start = segment_start[i]
        i_end = i_start + nseg - 1
        d_start = distances[i_start]
        d_end = distances[i_end]
        segment_ranges.append((d_start, d_end))
    # 3) 根据 path_connections 获取段间连续性，找出断点 distance
    # 定义断点集合
    breaks = []
    # 遍历path_connections的conn，找出断点 distance
    for i, conn in enumerate(path_connections):
        # conn 为 False 表示当前段与下一段不连接，即存在断点
        if conn is False:
            # 当前段的终点 distance 就是断点
            d_break = segment_ranges[i][1]   # 当前段的结束 distance
            breaks.append(d_break)
    # 4) 组装 header
    # 定义 header_lines 列表，保存 header 的每一行文本
    header_lines = []
    # 添加文件说明和基本信息
    header_lines.append("# Phonon dispersion data (MatterSim + phonopy)")
    # 添加 nqpoint 和 nmodes 信息
    header_lines.append(f"# NQPOINTS & NMODES: {{nqpoint}} {{nmodes}}")
    # 定义 shift 变量，初始为0
    shift = 0
    # 每段的起止对称高点名称(distance) 和 q 点数
    header_lines.append("# K-path segments:")
    for i, (d0, d1) in enumerate(segment_ranges):
        # 如果 d0 是断点 distance，则从当前段开始 shift+1
        if any(abs(d0 - bd) < 1e-12 for bd in breaks):
            shift += 1
        idx_start = i + shift
        idx_end   = i + shift + 1
        # 从 labels_info 获取高对称点名称，注意 idx_end 可能越界
        if idx_end < len(labels_info):
            label_start = labels_info[idx_start]
            label_end   = labels_info[idx_end]
        else:
            label_start = label_end = ""
        header_lines.append(
            f"#   Segment {{i+1}}(distance): {{label_start}}({{d0:.8f}}) -> {{label_end}}({{d1:.8f}})  (N = {{segment_nq[i]}})"
        )
    # 生成列名： distance + mode_1, mode_2, ..., mode_3N
    colnames = ["distance(1/A)"] + [f"mode_{{i+1}}(THz)" for i in range(nmodes)]
    header_lines.append("# " + "  ".join(colnames))
    header = "\\n".join(header_lines)
    # 保存文件
    print("Exporting phonon band matrix from memory...")
    out_path = os.path.join(work_dir, "phonon_band.dat")
    np.savetxt(out_path, mat, fmt="%.8f", header=header, comments="")
    print(f"Saved phonon_band.dat to {{out_path}}, shape = {{mat.shape}}")
export_phonon_band(phonons, ph.work_dir)
# 检查 total_dos.dat 是否自动生成
dos_path = os.path.join(ph.work_dir, "total_dos.dat")
if os.path.exists(dos_path):
    print(f"Detected auto-generated total_dos.dat at {{dos_path}}")
else:
    print("total_dos.dat was not generated automatically.")

# === 打印声子谱属性 ===
print("=== Phonon Calculation Finished ===")
print("Has imaginary phonon:", has_imag)
print("Phonon frequencies:", phonons)
"""

# -----------------------------
# 插件注册函数
# -----------------------------
def register_plugin(ScriptModule):
    #声明载入PhononDoubleLiteDat插件
    class PhononDoubleLiteDatScript(ScriptModule):
        #指定输入类型(1x1)
        supported_structure_mode = "1x1"
        #声明PhononDoubleLiteDat模式专有UI及参数
        def get_extra_parameters(self):
            return {
                "supercell": {
                    "type": "text",
                    "label": "超胞矩阵（如 2, 2, 2）",
                    "default": "2, 2, 2"
                },
                "displacement": {
                    "type": "number",
                    "label": "位移幅度 amplitude",
                    "default": 0.03,
                    "min": 0.01,
                    "max": 0.20,
                    "step": 0.01
                },
                "find_prim": {
                    "type": "checkbox",
                    "label": "自动寻找原胞 find_prim",
                    "default": False
                },
                "phonon_work_dir": {
                    "type": "text",
                    "label": "工作目录 work_dir",
                    "default": "./phonon_output"
                }
            }
        #脚本拼接指引
        def generate(self, state):
            #指定全局key
            state.supercell = state[self.param_key("supercell")]
            state.displacement = state[self.param_key("displacement")]
            state.find_prim = state[self.param_key("find_prim")]
            state.phonon_work_dir = state[self.param_key("phonon_work_dir")]
            #拼合脚本信息
            script = ""
            script += self.COMMON_HANDER
            script += self.generate_common_setup(state.model, state.device)  
            script += self.generate_structure_input(state)
            script += generate_phononDLD_block(state)
            #返回脚本
            return script  
        # 插件专属结果展示 UI 
        def render_result_ui(self):
            st.markdown("声子能带与 DOS 图谱")
            # 从全局状态获取工作目录
            work_dir = st.session_state.get(self.param_key("phonon_work_dir"), "./phonon_output")
            # 自动展示图谱
            plot_phonon_interactive(work_dir)

    #返回插件实例
    return PhononDoubleLiteDatScript