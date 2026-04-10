# 命令构建器模块
# 调用环境变量模块获取torchrun命令路径
from webui.core.env import SIM_ENV_TORCHRUN

# 辅助函数：根据参数值添加命令行参数
def add_arg(cmd, flag, value):
    if value not in (None, "", []):
        cmd.extend([flag, str(value)])
# 辅助函数：根据布尔值添加命令行标志
def add_flag(cmd, flag, is_set):
    if is_set:
        cmd.append(flag)
# 构建训练命令的函数，根据用户输入的参数构建完整的命令列表
def build_training_cmd(**kwargs):
    cmd = [
        SIM_ENV_TORCHRUN, "--nproc_per_node=1",
        "/opt/MatterSim/mattersim/src/mattersim/training/finetune_mattersim.py"
    ]

    add_arg(cmd, "--run_name", kwargs["run_name"])
    add_arg(cmd, "--load_model_path", kwargs["model"])
    add_arg(cmd, "--train_data_path", kwargs["train_data"])
    add_arg(cmd, "--valid_data_path", kwargs["val_data"])
    add_arg(cmd, "--device", kwargs["device"])
    add_arg(cmd, "--save_path", kwargs["save_dir"])
    add_arg(cmd, "--cutoff", kwargs["cutoff"])
    add_arg(cmd, "--threebody_cutoff", kwargs["threebody_cutoff"])
    add_arg(cmd, "--batch_size", kwargs["batch"])
    add_arg(cmd, "--lr", kwargs["lr"])
    add_arg(cmd, "--epochs", kwargs["epochs"])
    add_arg(cmd, "--early_stop_patience", kwargs["patience"])
    add_arg(cmd, "--seed", kwargs["seed"])
    add_arg(cmd, "--step_size", kwargs["step_size"])

    add_flag(cmd, "--include_forces", kwargs["include_forces"])
    add_arg(cmd, "--force_loss_ratio", kwargs["force_loss_ratio"])

    add_flag(cmd, "--include_stresses", kwargs["include_stresses"])
    add_arg(cmd, "--stress_loss_ratio", kwargs["stress_loss_ratio"])

    add_flag(cmd, "--save_checkpoints", kwargs["save_checkpoints"])
    add_arg(cmd, "--ckpt_interval", kwargs["ckpt_interval"])

    add_flag(cmd, "--re_normalize", kwargs["re_normalize"])
    add_arg(cmd, "--scale_key", kwargs["scale_key"])
    add_arg(cmd, "--shift_key", kwargs["shift_key"])
    add_arg(cmd, "--init_scale", kwargs["init_scale"])
    add_arg(cmd, "--init_shift", kwargs["init_shift"])
    add_flag(cmd, "--trainable_scale", kwargs["trainable_scale"])
    add_flag(cmd, "--trainable_shift", kwargs["trainable_shift"])

    add_flag(cmd, "--wandb", kwargs["wandb"])
    add_arg(cmd, "--wandb_api_key", kwargs["wandb_api_key"])
    add_arg(cmd, "--wandb_project", kwargs["wandb_project"])

    return cmd

#
def build_pretty_cmd(cmd):
    # 生成命令头
    header = f"torchrun {cmd[1]} {cmd[2]}"
    # 将 flag 和 value 合并成一行
    pretty_items = []
    i = 3
    while i < len(cmd):
        if cmd[i].startswith("--"):
        # flag
            if i + 1 < len(cmd) and not cmd[i+1].startswith("--"):
                # flag + value
                pretty_items.append(f"{cmd[i]} {cmd[i+1]}")
                i += 2
            else:
                # 单独 flag（布尔参数）
                pretty_items.append(cmd[i])
                i += 1
        else:
            i += 1
    # 生成多行命令
    pretty_cmd = header + " \\\n    " + " \\\n    ".join(pretty_items)
    return pretty_cmd
