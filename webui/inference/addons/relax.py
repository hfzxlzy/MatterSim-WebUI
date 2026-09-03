import streamlit as st

# -----------------------------
# 弛豫优化脚本片段
# -----------------------------
def generate_relax_block(state):
    files = state.file_list

    # 处理非晶体结构声明转译(filter=None)
    if state.relax_filter == "None":
        filter_arg = None
    else:
        filter_arg = f'"{state.relax_filter}"'

    # 单结构弛豫
    if len(files) == 1 and state.relax_mode == "单结构弛豫器（Relaxer）":
        rattle_code = ""
        if state.enable_rattle and state.rattle_std > 0:
            rattle_code = f"atoms.rattle(stdev={state.rattle_std})"
        if state.save_trajectory == False:
            return f"""
# === 单结构弛豫（ASE Relaxer） ===

atoms = structures[0]
atoms.calc = MatterSimCalculator(load_path=model_path,device=device)

# 可选扰动
{rattle_code}

relaxer = Relaxer(
    optimizer="{state.relax_optimizer}",
    filter={filter_arg},
    constrain_symmetry={state.constrain_symmetry}
)

success, relaxed_atoms = relaxer.relax(atoms, steps={state.max_steps})
print("=== Relaxation Finished (ASE Relaxer) ===")
print("Success:", success)
print("Final energy:", relaxed_atoms.get_potential_energy())
input_filename = files[0]
base_name = os.path.splitext(os.path.basename(input_filename))[0]  # 得到目标弛豫结构
relaxed_atoms.write("relaxed_structure_{{base_name}}.traj")
print(f"Saved relaxed structure to relaxed_structure_{{base_name}}.traj")

"""
        else:
            return f"""
# === 单结构弛豫（ASE Relaxer） ===

atoms = structures[0]
atoms.calc = MatterSimCalculator(load_path=model_path,device=device)

# 可选扰动
{rattle_code}

relaxer = Relaxer(
    optimizer="{state.relax_optimizer}",
    filter={filter_arg},
    constrain_symmetry={state.constrain_symmetry}
)
input_filename = files[0]
base_name = os.path.splitext(os.path.basename(input_filename))[0]  # 得到目标弛豫结构
success, relaxed_atoms = relaxer.relax(atoms, steps={state.max_steps}, trajectory=f"relaxed_structure_{{base_name}}.traj")
print("=== Relaxation Finished (ASE Relaxer) ===")
print("Success:", success)
print("Final energy:", relaxed_atoms.get_potential_energy())
print(f"Saved relaxed structure to relaxed_structure_{{base_name}}.traj")
"""

    # 多结构弛豫
    else:
        if state.save_trajectory  == False:
            return f"""
# === 批量结构弛豫（BatchRelaxer） ===

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

# 打印每个结构的初始/最终能量
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
        else:
            return f"""
# === 批量结构弛豫（BatchRelaxer） ===
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

# ① 打印每个结构的初始/最终能量
print("=== Relaxation Results ===")
for idx, (e0, e1) in enumerate(zip(initial_energies, relaxed_energies)):
    print(f"Structure {{idx+1}}: Initial = {{e0}} eV, Relaxed = {{e1}} eV")
# ② 对每个结构分别处理 traj
for (path, traj) in zip(files, relaxation_trajectories.values()):
    name = os.path.basename(path)
    stem = os.path.splitext(name)[0]
    outname = f"relaxed_structure_{{stem}}.traj"

    print(f"\\n=== Checking trajectory for {{stem}} ===")

    t = Trajectory(outname, 'w')

    prev_energy = None
    prev_force = None
    # ③ 遍历该结构的每一步
    for step, atoms in enumerate(traj):
        t.write(atoms)
        # 能量
        energy = atoms.info.get("total_energy")
        # 力
        try:
            forces = atoms.get_forces()
            max_force = forces.max()
        except Exception:
            max_force = None

        # 能量异常检查
        if prev_energy is not None and energy > prev_energy:
            print(f"⚠ Warning: Step {{step}}: Energy increased for {{stem}}: {{prev_energy}} -> {{energy}}")
        # 力异常检查（maxF 上升）
        if prev_force is not None and max_force is not None and max_force > prev_force:
            print(f"⚠ Warning: Step {{step}}: Max force increased for {{stem}}: {{prev_force}} -> {{max_force}}")

        prev_energy = energy
        prev_force = max_force

print(f"Saved full trajectory to {{outname}}")
"""

# -----------------------------
# 插件注册函数（关键）
# -----------------------------
def register_plugin(ScriptModule):
    #声明载入Relax插件
    class RelaxScript(ScriptModule):
        #指定输入类型(mx1)
        supported_structure_mode = "mx1"
        #声明Relax模式专有参数
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
                    "options": ["EXPCELLFILTER", "UNITCELLFILTER", "None"],
                    "default": "EXPCELLFILTER"
                },
                "save_trajectory": {
                    "type": "checkbox",
                    "label": "保存轨迹 save trajectory",
                    "default": False
                }
            }
            # 读取当前 filter 选择
            current_mode = st.session_state.get(self.param_key("relax_mode"), "单结构弛豫器（Relaxer）")
            #单结构弛豫参数
            if n == 1 :
                params.update({
                    "relax_mode": {
                    "type": "select",
                    "label": "弛豫器模式选择",
                    "options": ["单结构弛豫器（Relaxer）", "批量弛豫器（BatchRelaxer）"],
                    "default": "单结构弛豫器（Relaxer）"
                    }
                })
                # 读取当前 relax_mode 选择
                current_mode = st.session_state.get(self.param_key("relax_mode"), "单结构弛豫器（Relaxer）")
                # 只有单结构弛豫器模式器时才显示 Relax 相关配置选项
                if current_mode == "单结构弛豫器（Relaxer）":
                    # 读取当前 filter 选择
                    current_filter = st.session_state.get(self.param_key("relax_filter"), "EXPCELLFILTER")
                    # 只有 filter != None 时才显示 constrain_symmetry
                    if current_filter != "None":
                        params.update({
                            "constrain_symmetry": {
                                "type": "checkbox",
                                "label": "保持晶体对称性",
                                "default": True
                            }
                        })
                    params.update({
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
            state.save_trajectory = state[self.param_key("save_trajectory")]
            #单结构key选择
            if len(state.file_list) == 1:
                # 单结构才有 relax_mode
                state.relax_mode = state[self.param_key("relax_mode")]
                if state.relax_mode == "单结构弛豫器（Relaxer）":
                    # 自动联动：filter=None → constrain_symmetry=False
                    if state.relax_filter == "None":
                        state.constrain_symmetry = state[self.param_key("constrain_symmetry")]
                    else:
                        state.constrain_symmetry = state[self.param_key("constrain_symmetry")]
                    state.max_steps = state[self.param_key("max_steps")]
                    state.enable_rattle = state[self.param_key("enable_rattle")]
                    state.rattle_std = state[self.param_key("rattle_std")]
                else:
                    state.constrain_symmetry = state[self.param_key("constrain_symmetry")]
                    state.fmax = state[self.param_key("fmax")]
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