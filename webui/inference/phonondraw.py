# 声子计算结果绘图
# 调用os库
import os
# 调用numpy库
import numpy as np
# 调用plotly库
import plotly.graph_objects as go
# 调用plotly子库创建子图
from plotly.subplots import make_subplots
# 调用streamlit库
import streamlit as st

# 获取、修正K-path标签和位置并记录断点的函数
def parse_kpath_from_dat(band_path):
    # 定义一个字典来记录每个 distance 对应的标签
    labels = []
    # 定义一个字典来记录每个 distance 出现的位置列表
    positions = []
    # 定义一个列表来保存每个 segment 的 (label1, pos1, label2, pos2)
    segments = []
    #定义断点位置集合
    breaks = []
    break_label_pairs = []
    # LaTeX 包裹清洗函数，例如 $\mathrm{X}$ → X
    def clean_label(label):
        label = label.replace("$", "")    # 去掉$符号
        label = label.replace("\\mathrm{", "")    # 去掉\\mathrm{
        label = label.replace("}", "")    # 去掉}
        label = label.replace("\\Gamma", "Γ")    # 特例：\Gamma→Γ
        # 其他 LaTeX 转义可以在这里继续添加
        #返回清洗后的标签
        return label.strip()  
    # 将 band_path 位置的文件中 Segment 行解析出标签和位置
    with open(band_path, "r") as f:
        for line in f:
            # 如果行中包含 Segment 和 distance 关键词，说明这是一个高对称点段的描述行(例如:  $\Gamma$(0.00000000) -> $\mathrm{X}$(0.07573607))
            if "Segment" in line and "distance" in line:
                # 解析行内容，提取出起点和终点的标签及位置
                parts = line.split(":")[1].strip()
                # 分割起点(left:$\Gamma$(0.00000000))和终点(right:$\mathrm{X}$(0.07573607))
                left, right = parts.split("->")
                # 从起点读取标签($\Gamma$)
                raw_label1 = left.split("(")[0].strip()
                # 从起点读取位置(浮点数 0.00000000)
                pos1 = float(left.split("(")[1].split(")")[0])
                # 从终点读取标签($\mathrm{X}$)
                raw_label2 = right.split("(")[0].strip()
                # 从终点读取位置(浮点数 0.07573607)
                pos2 = float(right.split("(")[1].split(")")[0])
                # 清洗标签
                label1 = clean_label(raw_label1)
                label2 = clean_label(raw_label2)
                # 添加起点(["Γ", "X", ...])和位置([0.0, 0.07573607, ...])到列表
                labels.append(label1)
                positions.append(pos1)
                # 记录段信息
                segments.append((label1, pos1, label2, pos2))
        #从最后一段信息中获取最后一个标签和位置
        last_label2 = segments[-1][2]
        last_pos2 = segments[-1][3]
        # 补齐最后一个终点
        labels.append(last_label2)
        positions.append(last_pos2)
    # 根据 segments 信息找出断点
    for i in range(len(segments) - 1):
        # 当前段的终点信息
        _, _, end_label, end_pos = segments[i]
        # 下一段的起点信息
        next_label, next_pos, _, _ = segments[i + 1]
        # 如果当前段的终点标签与下一段的起点标签不同，说明这是一个断点
        if end_label != next_label:
            breaks.append(end_pos)
            idx = positions.index(end_pos)
            labels[idx] = f"{end_label}|{next_label}"
    # 返回标签列表、位置列表和断点列表
    return labels, positions, breaks

# 使用 phonon_band.dat 和 total_dos.dat 绘制交互式声子色散 + DOS 图的函数
def plot_phonon_interactive(work_dir):
    # 声子色散构建文件路径(phonon_band.dat)
    band_path = os.path.join(work_dir, "phonon_band.dat")
    # 声子态密度构建文件路径(total_dos.dat)
    dos_path = os.path.join(work_dir, "total_dos.dat")
    # === 文件检查 ===
    if not os.path.exists(band_path):
        st.error(f"未找到 {band_path}，请先运行声子计算。")
        return
    if not os.path.exists(dos_path):
        st.error(f"未找到 {dos_path}，请先运行声子计算。")
        return
    # === 读取数据 ===
    band_data = np.loadtxt(band_path, comments="#")
    dos_data = np.loadtxt(dos_path, comments="#")
    # === 数据处理 ===
    # 从 band_data 中分离出 distance (第一列)和频率(其余列)矩阵
    distances = band_data[:, 0]
    freqs = band_data[:, 1:]
    # 从 dos_data 中分离出频率和态密度
    dos_freq = dos_data[:, 0]
    dos_val = dos_data[:, 1]
    # 从 band_path 中解析出K-path标签信息（labels_info）和 K-path位置（tick_positions）、断点位置（break_positions）
    labels_info, tick_positions, break_positions = parse_kpath_from_dat(band_path)
    # === 绘图 ===
    fig = go.Figure()
    # === DOS ===
    # 绘制态密度曲线，x轴为态密度，y轴为频率，使用第二个 x 轴（x2）
    fig.add_trace(go.Scatter(
        x=dos_val,    # x轴为态密度
        y=dos_freq,    # y轴为频率
        mode="lines",    # 线条模式：线连接
        line=dict(color="blue", width=2),    # 线条样式：蓝色，宽度2
        xaxis="x2",    # 指定使用第二个 x 轴（x2）
        yaxis="y2",    # 指定使用第二个 y 轴（y2）
        hovertemplate="DOS: %{x:.3f}<br>Freq: %{y:.3f} THz",    # 鼠标悬停提示：显示态密度和频率
        name="DOS"    # 图例名称：DOS
        )
    )
    # === 绘制每条声子能带 ===
    # 从 freqs 矩阵中逐列绘制，每列对应一个声子模式，x轴为 distance，y轴为频率
    for i in range(freqs.shape[1]):
        x = []
        y = []
        # 遍历每个 distance 和对应的频率，构建 x 和 y 列表
        for j in range(len(distances)):
            x.append(distances[j])
            y.append(freqs[j, i])
            # 控制断点宽度
            gap = 5e-4
            # 如果到达断点 → 插入 NaN 断开线条
            if any(abs(distances[j] - bp) < 1e-8 for bp in break_positions):
                # 在断点位置插入一个 gap，并将频率设置为 NaN 来断开线条
                x.append(distances[j] + gap)
                y.append(np.nan)
        # 绘制第 i 条声子能带
        fig.add_trace(go.Scatter(
            x=x,    # x轴为x
            y=y,    # y轴为y
            mode="lines",    # 线条模式：线连接
            line=dict(color="red", width=1),    # 线条样式：红色，宽度1
            hovertemplate="Distance: %{x:.3f}<br>Freq: %{y:.3f} THz",    # 鼠标悬停提示：显示 distance 和频率
            name=f"Mode {i+1}"    # 图例名称：Mode 1, Mode 2, ...
            )
        )
    # === 布局 ===
    # band_data 频率范围
    band_y_min = freqs.min()
    band_y_max = freqs.max()
    # dos_data 频率范围
    dos_y_min = dos_freq.min()
    dos_y_max = dos_freq.max()
    # 统一 y 轴范围：取两者的最大区间
    y_min = min(band_y_min, dos_y_min)
    y_max = max(band_y_max, dos_y_max)
    # 增加一点 y 轴范围的 padding，使图表更美观
    padding = (y_max - y_min) * 0.05
    y_min -= padding
    y_max += padding
    # 设置标题、轴标签、图例和交互模式
    fig.update_layout(
        # 图标标题
        title={
            'text': 'Phonon Dispersion + DOS (Interactive)',    # 标题文本
            'y': 0.98,    # 标题靠上
            'x': 0.5,    # 标题居中
            'xanchor': 'center',    # 标题水平锚定在中心
            'yanchor': 'top'    # 标题垂直锚定在顶部
        },
        # x 轴设置
        xaxis=dict(
            title='Wave vector path',    # x轴标题
            tickmode='array',    # 刻度模式：使用自定义刻度位置
            tickvals=tick_positions,    # 刻度位置：从文件解析得到的高对称点位置
            ticktext=labels_info,    # 刻度标签：从文件解析得到的高对称点标签
            side='bottom',    # 高对称点在下方
            domain=[0, 0.75]    # 主 x 轴占图表的前75%
        ),
        # x2 轴设置
        xaxis2=dict(
            title='Density of states',    # x2轴标题
            side='top',    # DOS 的 x 轴放到上方
            overlaying=None,    # 不与主 x 轴共享坐标空间
            matches=None,    # 不强制刻度一致
            showgrid=False,    # 不显示网格线
            ticks='outside',    # 刻度线在外侧
            domain=[0.755, 0.935]      # DOS 区域占右侧 20%
        ),
        # y 轴设置
        yaxis=dict(
            title='Frequency (THz)',    # y轴标题
            side='left',    # y 轴放到左侧
            anchor='x',    # 锚定在 x 轴上
            showgrid=True,    # 显示网格线
            zeroline=False,    # 显示 y=0 的基准线
            range=[y_min, y_max]     # y 轴范围根据数据自动调整
        ),
        #  y2 轴设置
        yaxis2=dict(
            title='Frequency (THz)',    # y2轴标题
            side='right',    # y2 轴放到右侧
            overlaying='y',    # 与主 y 轴共享坐标空间
            anchor='x2',    # 锚定在 x2 轴上
            position=0.94,    # y2 轴位置靠右
            showgrid=True,    # 显示网格线
            ticks='outside',    # 刻度线在外侧
            range=[y_min, y_max]     # y2 轴与主 y 轴保持相同范围
        ),  
        #legend=dict(x=0.8, y=1),    # 图例位置：右上角
        template='plotly_white',    # 使用白色主题
        hovermode='closest',    # 鼠标悬停模式：显示最近的数据点
        #width=900,    # 图表宽度
        height=600,    # 图表高度
        modebar_add=["toImage"]    # 添加保存为图片按钮
    )
    # === 蓝色十字参考线 ===
    # 鼠标悬停时显示参考线横轴
    fig.update_xaxes(
        showspikes=True,    # 显示参考线
        spikemode="across",    # 参考线模式：横跨整个图表
        spikesnap="cursor",    # 参考线对齐方式：跟随鼠标光标
        spikecolor="blue",    # 参考线颜色：蓝色
        spikethickness=1    # 参考线宽度：1
        )
    # 鼠标悬停时显示参考线纵轴
    fig.update_yaxes(
        showspikes=True,    # 显示参考线
        spikemode="across",    # 参考线模式：横跨整个图表
        spikesnap="cursor",    # 参考线对齐方式：跟随鼠标光标
        spikecolor="blue",    # 参考线颜色：蓝色
        spikethickness=1    # 参考线宽度：1
        )
    # 显示图表(填满宽度)
    st.plotly_chart(fig, width="stretch")