# 脚本通用片段生成模块

#通用库调用头文件
COMMON_HANDER =  """
import os
import torch
import numpy as np
from ase.io import read
from loguru import logger
from ase.units import GPa
from ase.build import bulk
from ase.visualize import view
from ase.data.colors import jmol_colors
from mattersim.applications.relax import Relaxer
from mattersim.forcefield.potential import Potential
from mattersim.applications.phonon import PhononWorkflow
from mattersim.applications.batch_relax import BatchRelaxer
from mattersim.datasets.utils.build import build_dataloader
from mattersim.forcefield.potential import MatterSimCalculator
"""

#模型、设备通用调用片段函数
def generate_common_setup(model, device):
    return f"""
model_path = "{model}"
device = "{device}"
print("Using model:", model_path)
print("Running on device:", device)
"""