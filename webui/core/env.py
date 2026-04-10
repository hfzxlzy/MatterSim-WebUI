# 定义环境变量和路径常量
import os
# MatterSim虚拟环境中的Python路径
SIM_ENV_PYTHON = "/your/path/of/MatterSim/sim_env/bin/python3"
# MatterSim虚拟环境中的torchrun路径
SIM_ENV_TORCHRUN = "/your/path/of/MatterSim/sim_env/bin/torchrun"
# 历史记录文件路径，用于保存/读取历史记录
HISTORY_FILE = os.path.expanduser("/your/path/of/MatterSim/.mattersim_runs.json")