# 训练预设位置模块
# 模型预设路径列表，包含多个示例模型文件的路径
MODEL_PRESETS=["/your/path/of/MatterSim/models/mattersim-v1.0.0-1M.pth", "/your/path/of/MatterSim/models/mattersim-v1.0.0-5M.pth"]
# 训练数据预设路径列表，包含多个示例数据集的路径
TRAIN_DATA_PRESETS=["/your/path/of/MatterSim/mattersim/tests/data/high_level_water.xyz", "/your/path/of/MatterSim/mattersim/tests/data/mp-149_Si2.cif", "/your/path/of/MatterSim/mattersim/tests/data/mp-2998_BaTiO3.cif", "/your/path/of/MatterSim/mattersim/tests/data/mp-66_C2.cif"]
# 验证数据预设路径列表，包含多个示例数据集的路径
VAL_DATA_PRESETS=["/your/path/of/MatterSim/mattersim/data/benchmarks/alexandria-random-1k.xyz", "/your/path/of/MatterSim/mattersim/data/benchmarks/mpf-alkali-TP.xyz", "/your/path/of/MatterSim/mattersim/data/benchmarks/mpf-TP.xyz", "/your/path/of/MatterSim/mattersim/data/benchmarks/mptrj-highest-stress-1k.xyz", "/your/path/of/MatterSim/mattersim/data/benchmarks/mptrj-random-1k.xyz", "/your/path/of/MatterSim/mattersim/data/benchmarks/random-TP.xyz"]
# 保存目录预设路径列表，包含多个示例保存目录的路径
SAVE_DIR_PRESETS=["/your/path/of/MatterSim/models/"]