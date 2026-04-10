import streamlit as st

# -----------------------------
# 声子计算脚本片段
# -----------------------------
def generate_phonon_block(state):
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

print("=== Phonon Calculation Finished ===")
print("Has imaginary phonon:", has_imag)
print("Phonon frequencies:", phonons)
"""

# -----------------------------
# 插件注册函数
# -----------------------------
def register_plugin(ScriptModule):
    #定义Phonon插件
    class PhononScript(ScriptModule):
        #指定输入类型(1x1)
        supported_structure_mode = "1x1"
        #定义Phonon模式专有参数
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
            script += generate_phonon_block(state)
            #返回脚本
            return script   
    #返回插件实例
    return PhononScript