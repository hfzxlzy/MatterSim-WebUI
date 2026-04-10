# -----------------------------
# 结构预测脚本输出片段
# -----------------------------
def generate_predict_block(state):
    return """
# 构建 dataloader
dataloader = build_dataloader(structures, only_inference=True)

# 加载模型
potential = Potential.from_checkpoint(load_path=model_path,device=device)

# 推理
energies, forces, stresses = potential.predict_properties(
    dataloader,
    include_forces=True,
    include_stresses=True
)

# 输出
print("=== Predict Results ===")
for i, (e, f, s) in enumerate(zip(energies, forces, stresses)):
    natoms = len(structures[i])
    avg_e = e / natoms

    print(f"\\n--- Structure {i+1} ---")
    print("Total energy (eV):", e)
    print("Average energy per atom (eV):", avg_e)
    print("Forces (eV/Å):")
    print(f)
    print("Stresses (GPa):")
    print(s)
    print("Stresses (eV/Å^3):")
    print(np.array(s) * GPa)
"""

# -----------------------------
# 插件注册函数（关键）
# -----------------------------
def register_plugin(ScriptModule):
    #定义Predict插件
    class PredictScript(ScriptModule):
        #指定输入类型(mxn)
        supported_structure_mode = "mxn"
        #定义Predict模式专有参数
        def get_extra_parameters(self):
            return {
                "repeat_n": {
                "type": "number",
                "label": "各结构重复次数 n",
                "default": 1,
                "min": 1,
                "max": 999
            }
        }
        def generate(self, state):
            #指定全局key
            state.repeat_n = state[self.param_key("repeat_n")]
            #拼合脚本信息
            script = ""
            script += self.COMMON_HANDER
            script += self.generate_common_setup(state.model, state.device)  
            script += self.generate_structure_input(state)
            script += generate_predict_block(state)
            #返回脚本
            return script   
    #返回插件实例        
    return PredictScript
