<p align="right">
 <a href="README_EN.md">English</a> | 中文
</p>

# MatterSim WebUI
MatterSim WebUI 是一个基于 Streamlit 的图形界面，用于可视化、管理和运行 MatterSim 的推理与训练任务。  
本项目采用模块化架构设计，支持插件扩展、结构可视化、声子计算、结构优化、模型训练等功能。

---

## 功能特性

- **模块化架构**：代码按功能分层，易于维护与扩展  
- **插件系统（Addons）**：支持 predict / relax / phonon 等推理模式，可轻松扩展新插件  
- **结构可视化工具**：基于 ASE，实现结构构建、编辑、渲染  
- **推理链路（Inference Pipeline）**：UI → 参数生成(py_parameters) → 脚本生成(py_script) → 推理核心 (infer_core) → MatterSimCalculator → 结果  
- **训练模块（Training）**：支持分布式训练命令构建与执行  
- **实时日志与历史记录**：便于调试与追踪任务状态  

---

## 快速开始

### 1. 安装 MatterSim

请按照 MatterSim 官方文档安装（支持 pip / 源码编译）：
https://github.com/microsoft/mattersim/blob/main/README.md#install-from-source-code


### 2. 安装WebUI依赖

```bash
pip install streamlit psutil py3Dmol pandas matplotlib
```

### 3. 放置 WebUI

将该项目中`Webui`文件夹放入你自己的 MatterSim 安装路径，例如：
`/your/path/of/MatterSim/`

### 4. 修改路径

在运行 WebUI 之前，请先修改以下文件中的路径，将其中的  
`/your/path/of/MatterSim` 替换为你自己的 MatterSim 安装路径：
- `webui/core/env.py`
- `webui/training/presets.py`
- `webui/training/cmd_builder.py`
- `webui/inference/ui.py`

### 5. 运行

修改完成后，使用以下命令运行 WebUI（同样请替换路径）：
```bash
/your/path/of/MatterSim/sim_env/bin/python3 -m streamlit run /your/path/of/MatterSim/webui/webui1.2.1.py
```

---

## 插件系统（Addons）

所有推理插件位于：
webui/inference/addons/

每个插件只需实现：
- 参数渲染函数
- 脚本生成函数
- 推理执行函数
插件会被自动加载，无需修改核心代码。

---

## 训练模块（Training）
训练模块包含：
- cmd_builder.py：构建 torchrun 命令
- executor.py：执行训练任务
- presets.py：训练参数预设
- ui.py：训练界面

---

## 参考文献（Reference）
  
如果你在科研或项目中使用 MatterSim-WebUI，请同时引用 MatterSim 的原始预印本：
```bash
@article{yang2024mattersim,
      title={MatterSim: A Deep Learning Atomistic Model Across Elements, Temperatures and Pressures},
      author={Han Yang and Chenxi Hu and Yichi Zhou and Xixian Liu and Yu Shi and Jielan Li and Guanzhi Li and Zekun Chen and Shuizhou Chen and Claudio Zeni and Matthew Horton and Robert Pinsler and Andrew Fowler and Daniel Zügner and Tian Xie and Jake Smith and Lixin Sun and Qian Wang and Lingyu Kong and Chang Liu and Hongxia Hao and Ziheng Lu},
      year={2024},
      eprint={2405.04967},
      archivePrefix={arXiv},
      primaryClass={cond-mat.mtrl-sci},
      url={https://arxiv.org/abs/2405.04967},
      journal={arXiv preprint arXiv:2405.04967}
}
```

