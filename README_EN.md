<p align="right">
 English | <a href="README.md">中文</a>
</p>

#  **MatterSim WebUI **

MatterSim WebUI is a Streamlit‑based graphical interface for visualizing, managing, and running inference and training tasks with **MatterSim**.  
The project adopts a modular architecture and supports plugin extensions, structure visualization, phonon calculations, structure relaxation, and model training.

---

## Features

- **Modular Architecture**  
  Cleanly separated modules for easy maintenance and extension.

- **Plugin System (Addons)**  
  Supports inference modes such as *predict*, *relax*, and *phonon*.  
  New plugins can be added without modifying core code.

- **Structure Visualization Tools**  
  Built on ASE, supporting structure building, editing, and rendering.

- **Unified Inference Pipeline**  
  UI → Parameter generation (`py_parameters`) → Script generation (`py_script`) → Inference core (`infer_core`) → MatterSimCalculator → Results

- **Training Module**  
  Supports distributed training command construction and execution.

- **Real‑time Logs & History Tracking**  
  Convenient for debugging and monitoring task status.

---

## Quick Start

### 1. Install MatterSim

Follow the official MatterSim installation guide (pip or source build):  
https://github.com/microsoft/mattersim/blob/main/README.md#install-from-source-code

---

### 2. Install WebUI Dependencies

```bash
pip install streamlit psutil py3Dmol pandas matplotlib
```

---

### 3. Place the WebUI Folder

Copy the `webui` folder from this project into your MatterSim installation directory, e.g.:

```
/your/path/of/MatterSim/
```

---

### 4. Configure Paths

Before running the WebUI, update the following files and replace  
`/your/path/of/MatterSim` with your actual MatterSim installation path:

- `webui/core/env.py`
- `webui/training/presets.py`
- `webui/inference/ui.py`

---

### 5. Run the WebUI

After updating the paths, launch the WebUI with:

```bash
/your/path/of/MatterSim/sim_env/bin/python3 -m streamlit run /your/path/of/MatterSim/webui/webui1.2.1.py
```

---

## Plugin System (Addons)

All inference plugins are located in:

```
webui/inference/addons/
```

Each plugin only needs to implement:

- Parameter rendering function  
- Script generation function  
- Inference execution function  

Plugins are automatically loaded—no changes to core code are required.

---

## Training Module

The training module includes:

- `cmd_builder.py` — Builds `torchrun` commands  
- `executor.py` — Executes training tasks  
- `presets.py` — Training parameter presets  
- `ui.py` — Training interface  

---

## Reference

If you use MatterSim-WebUI in your research or project, please also cite the original MatterSim preprint: 
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
