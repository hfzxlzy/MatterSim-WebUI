import streamlit as st

# -----------------------------
# 弛豫优化脚本片段
# -----------------------------
def generate_relax_block(state):
    files = state.file_list

    # 单结构松弛
    if len(files) == 1:
        rattle_code = ""
        if state.enable_rattle and state.rattle_std > 0:
            rattle_code = f"atoms.rattle(stdev={state.rattle_std})"

        return f"""
# === 单结构松弛（ASE Relaxer） ===

atoms = structures[0]
atoms.calc = MatterSimCalculator(load_path=model_path,device=device)

# 可选扰动
{rattle_code}

relaxer = Relaxer(
    optimizer="{state.relax_optimizer}",
    filter="{state.relax_filter}",
    constrain_symmetry={state.constrain_symmetry}
)

success, relaxed_atoms = relaxer.relax(atoms, steps={state.max_steps})
print("=== Relaxation Finished (ASE Relaxer) ===")
print("Success:", success)
print("Final energy:", relaxed_atoms.get_potential_energy())
relaxed_atoms.write("relaxed_structure.traj")
"""

    # 多结构松弛
    else:
        return f"""
# === 批量结构松弛（BatchRelaxer） ===

potential = Potential.from_checkpoint(load_path=model_path,device=device)

relaxer = BatchRelaxer(
    potential,
    fmax={state.fmax},
    filter="{state.relax_filter}",
    optimizer="{state.relax_optimizer}"
)

relaxation_trajectories = relaxer.relax(structures)

relaxed_structures = [traj[-1] for traj in relaxation_trajectories.values()]
relaxed_energies = [s.info['total_energy'] for s in relaxed_structures]

initial_structures = [traj[0] for traj in relaxation_trajectories.values()]
initial_energies = [s.info['total_energy'] for s in initial_structures]

print("=== Relaxation Results ===")
for i, (e0, e1) in enumerate(zip(initial_energies, relaxed_energies)):
    print(f"Structure {{i+1}}: Initial = {{e0}} eV, Relaxed = {{e1}} eV")

for (path, atoms) in zip(files, relaxed_structures):
    name = os.path.basename(path)
    stem = os.path.splitext(name)[0]
    outname = f"relaxed_structure_{{stem}}.traj"
    atoms.write(outname)
    print(f"Saved relaxed structure to {{outname}}")
"""

# -----------------------------
# 插件注册函数（关键）
# -----------------------------
def register_plugin(ScriptModule):
    #定义Relax插件
    class RelaxScript(ScriptModule):
        #指定输入类型(mx1)
        supported_structure_mode = "mx1"
        #定义Relax模式专有参数
        def get_extra_parameters(self):
            file_list = st.session_state.get("file_list", [])
            n = len(file_list)
            #通用弛豫参数
            params = {
                "relax_optimizer": {
                    "type": "select",
                    "label": "优化器 optimizer",
                    "options": ["BFGS", "LBFGS", "FIRE"],
                    "default": "BFGS"
                },
                "relax_filter": {
                    "type": "select",
                    "label": "过滤器 filter",
                    "options": ["EXPCELLFILTER", "UNITCELLFILTER"],
                    "default": "EXPCELLFILTER"
                },
            }
            #单结构弛豫参数
            if n == 1:
                params.update({
                    "constrain_symmetry": {
                        "type": "checkbox",
                        "label": "保持晶体对称性",
                        "default": True
                    },
                    "max_steps": {
                        "type": "number",
                        "label": "最大步数 steps",
                        "default": 200,
                        "min": 1,
                        "max": 5000
                    },
                    "enable_rattle": {
                        "type": "checkbox",
                        "label": "扰动初始结构 rattle",
                        "default": False
                    },
                    "rattle_std": {
                        "type": "number",
                        "label": "扰动标准差（Å）",
                        "default": 0.1,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01
                    },
                })
            #多结构弛豫参数
            else:
                params.update({
                    "fmax": {
                        "type": "number",
                        "label": "收敛阈值 fmax",
                        "default": 0.05,
                        "min": 0.01,
                        "max": 1.0,
                        "step": 0.01
                    }
                })

            return params

        def generate(self, state):
            #指定全局key
            state.relax_optimizer = state[self.param_key("relax_optimizer")]
            state.relax_filter = state[self.param_key("relax_filter")]
            #单结构key选择
            if len(state.file_list) == 1:
                state.constrain_symmetry = state[self.param_key("constrain_symmetry")]
                state.max_steps = state[self.param_key("max_steps")]
                state.enable_rattle = state[self.param_key("enable_rattle")]
                state.rattle_std = state[self.param_key("rattle_std")]
            #多结构key选择
            else:
                state.fmax = state[self.param_key("fmax")]
            #拼合脚本信息
            script = ""
            script += self.COMMON_HANDER
            script += self.generate_common_setup(state.model, state.device)  
            script += self.generate_structure_input(state)
            script += generate_relax_block(state)
            #返回脚本
            return script   
    #返回插件实例
    return RelaxScript