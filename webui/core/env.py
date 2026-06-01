# 定义环境变量和路径常量
import os

# 自定义项目根目录
MATTERSIM_ROOT =  "/your/path/of/MatterSim"

# MatterSim虚拟环境中的Python主路径
SIM_ENV_PYTHON = os.path.join(MATTERSIM_ROOT, "sim_env/bin/python3")
# MatterSim虚拟环境中的trchrun模块路径
SIM_ENV_TORCHRUN = os.path.join(MATTERSIM_ROOT, "sim_env/bin/torchrun")

# 历史记录文件路径，用于保存/读取历史记录
HISTORY_FILE = os.path.expanduser(os.path.join(MATTERSIM_ROOT, ".mattersim_runs.json"))

# 模型文件路径
MODELS_DIR = os.path.join(MATTERSIM_ROOT, "models")
# 测试数据路径
DATA_DIR = os.path.join(MATTERSIM_ROOT, "mattersim/tests/data")
# 基准文件位置
BENCHMARK_DIR = os.path.join(MATTERSIM_ROOT, "mattersim/data/benchmarks")
# 微调入口脚本位置
FINETUNE_MATTERSIM_DIR = os.path.join(MATTERSIM_ROOT, "mattersim/src/mattersim/training/finetune_mattersim.py")

# 临时文件位置
TMP = os.path.join(MATTERSIM_ROOT, "tmp")
# 自动检测并创建 tmp 目录
os.makedirs(TMP, exist_ok=True)

# 模型预设路径列表，包含多个示例模型文件的路径
MODEL_PRESETS = [
    os.path.join(MODELS_DIR, "mattersim-v1.0.0-1M.pth"),
    os.path.join(MODELS_DIR, "mattersim-v1.0.0-5M.pth"),
]

# 训练数据预设路径列表，包含多个示例数据集的路径
TRAIN_DATA_PRESETS = [
    os.path.join(DATA_DIR, "high_level_water.xyz"),
    os.path.join(DATA_DIR, "mp-149_Si2.cif"),
    os.path.join(DATA_DIR, "mp-2998_BaTiO3.cif"),
    os.path.join(DATA_DIR, "mp-66_C2.cif"),
]

# 验证数据预设路径列表，包含多个示例数据集的路径
VAL_DATA_PRESETS = [
    os.path.join(BENCHMARK_DIR, "alexandria-random-1k.xyz"),
    os.path.join(BENCHMARK_DIR, "mpf-alkali-TP.xyz"),
    os.path.join(BENCHMARK_DIR,"mpf-TP.xyz"),
    os.path.join(BENCHMARK_DIR, "mptrj-highest-stress-1k.xyz"),
    os.path.join(BENCHMARK_DIR, "mptrj-random-1k.xyz"),
    os.path.join(BENCHMARK_DIR, "random-TP.xyz"),
]

# 微调后模型保存目录预设路径列表，包含多个示例保存目录的路径
SAVE_DIR_PRESETS = [MODELS_DIR]