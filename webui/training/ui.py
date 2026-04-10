# 训练界面模块
# 调用streamlit库构建训练界面
import streamlit as st
# 调用time库获取当前时间
import time
# 调用threading库实现训练过程的多线程执行
import threading

from webui.core.env import SIM_ENV_TORCHRUN
from webui.core.runner import run_command
from webui.core.history import load_history, save_history
# 调用训练命令构建器模块中的函数构建训练命令
from webui.training.cmd_builder import build_training_cmd, build_pretty_cmd
from webui.training.executor import start_training
# 调用训练预设位置模块中的预设路径列表
from webui.training.presets import MODEL_PRESETS, TRAIN_DATA_PRESETS, VAL_DATA_PRESETS, SAVE_DIR_PRESETS

# 训练界面组件
def show_training_page():
    st.subheader("训练参数")
    coll, colr = st.columns([1, 1])
    with coll:
        #[变量名] = st.[输入框类型]("[显示名称]", help="[帮助信息]", value=[默认值])
        run_name = st.text_input(
            #[显示名称]
            "运行名称",
            #help=[帮助信息]
            help="The name of the run. Default is “example_[time]”.  \n本次微调项目名称",
            #placeholder=[占位符]
            placeholder="微调项目名称",
            #value=[默认值]
            value=f"example_{int(time.time())}",
        )
        model = st.selectbox(
            #[显示名称]
            "预设模型文件路径",
            #help=[帮助信息]
            help="Path to load the pre-trained model. Default is None.  \n可从下拉列表中选择预训练模型，或输入自定义模型路径，默认为None",
            #options=[选项列表]
            options=MODEL_PRESETS,
            #index=[默认选项索引]
            index=None,
            #placeholder=[占位符]
            placeholder="选择预训练模型或输入模型路径",
            #accept_new_options=[是否接受新选项]
            accept_new_options=True
        )
        train_data = st.selectbox(
            #[显示名称]
            "训练数据路径",
            #help=[帮助信息]
            help="Path to the training data file. Supports various file types readable by ASE (e.g., .xyz, .traj, .cif) and .pkl files.  \n可从下拉列表中选择训练数据，或输入自定义训练数据路径",
            #options=[选项列表]
            options=TRAIN_DATA_PRESETS,
            #index=[默认选项索引]
            index=None,
            #placeholder=[占位符]
            placeholder="选择预训练模型或输入训练数据路径",
            #accept_new_options=[是否接受新选项]
            accept_new_options=True
        )
    with colr:
        device = st.radio(
            #[显示名称]
            "训练单元选择",
            #help=[帮助信息]
            help="Device to use for training, either “cuda” or “cpu”. Default is “cuda”.  \n选择用于训练的单元，cuda表示使用GPU，cpu表示使用CPU，默认为cuda",
            #options=[选项列表]
            options=["cuda", "cpu"],
            #horizontal=[是否横向排布]
            horizontal=True,
            #index=[默认选项索引]
            index=0
        )
        val_data = st.selectbox(
            "基准数据路径",
            help="Path to the validation data file. Default is None.  \n可从下拉列表中选择基准数据，或输入自定义基准数据路径，默认为None",
            options=VAL_DATA_PRESETS,
            index=None,
            placeholder="选择预训练模型或输入基准数据路径",
            accept_new_options=True
        )
        save_dir = st.selectbox(
            "保存目录",
            help=" Path to save the trained model. Default is “./results/[run_name]”.  \n可从下拉列表中选择训练后模型保存目录，或输入自定义保存目录，默认为./results/[run_name]",
            options=SAVE_DIR_PRESETS,
            index=None,
            placeholder="选择训练后模型保存目录",
            accept_new_options=True
        )
    cold, cole, colf, colg = st.columns([1, 1, 1, 1])
    with cold:
        batch = st.number_input(
            "Batch Size",
            help="Batch size for training. Default is 16.  \n训练的批量大小，默认为16",
            value=16
        )
        lr = st.number_input(
            "Learning Rate",
            help="Learning rate for the optimizer. Default is 2e-4.  \n优化器的学习率，默认为2e-4",
            value=2e-4,
            format="%.1e"
        )
    with cole:
        epochs = st.number_input(
            "Epochs",
            help="Number of training epochs. Default is 1000.  \n训练的总epoch数，默认为1000",
            value=1000
        )
        patience = st.number_input(
            "Earlyp Stop Patience",
            help="Patience for early stopping. Default is 10.  \n早停的耐心值，默认为10",
            value=10
        )
    with colf:
        seed = st.number_input(
            "Seed",
            help="Random seed for reproducibility. Default is 42.  \n用于结果复现的随机种子，默认为42",
            value=42
        )
        step_size = st.number_input(
            "Step Size",
            help="Step size for the learning rate scheduler. Default is 10.  \n学习率调度器的步长，默认为10",
            value=10
        )
    with colg:
        cutoff = st.number_input(
            "Cutoff Distance",
            help="Cutoff distance for neighbor list construction. Default is 5.0 Å.  \n用于构建邻居列表的截断距离，单位为埃，默认为5.0",
            value=5.0,
            min_value=0.1,
            max_value=20.0,
            format="%.2f"
        )
        threebody_cutoff = st.number_input(
            "Three-body Cutoff Distance",
            help="Cutoff distance for three-body interactions. Must be less than or equal to the neighbor list cutoff. Default is 4.0 Å.  \n用于三体相互作用的截断距离，必须小于等于邻居列表截断距离，单位为埃，默认为4.0",
            value=4.0,
            min_value=0.1,
            # 自动限制不能超过 cutoff
            max_value=cutoff,
            format="%.2f"
        )
        
    colu, colv, colw = st.columns([1, 1, 1])
    with colu:
        include_forces = st.checkbox(
            "Include Forces",
            help="Whether to include forces in the training. Default is True.\n是否在训练中包含力项，默认为True",
            value=True
        )
        if include_forces:
            with st.expander("Force loss ratio"):
                force_loss_ratio= st.number_input(
                "Force Loss Ratio",
                help="Ratio of force loss in the total loss. Default is 1.0.  \n总损失中力损失的比例，默认为1.0",
                value=1.0,
                min_value=0.1,
                max_value=20.0,
                format="%.2f"
                )
        else:
            force_loss_ratio = None
    with colv:
        include_stresses = st.checkbox(
            "Include Stresses",
            help="Whether to include stresses in the training. Default is False.\n是否在训练中包含应力项，默认为False",
            value=False
        )
        if include_stresses:
            with st.expander("Stress loss ratio"):
                stress_loss_ratio= st.number_input(
                "Stress Loss Ratio",
                help="Ratio of stress loss in the total loss. Default is 0.1.  \n总损失中应力损失的比例，默认为0.1",
                value=0.1, 
                min_value=0.0,
                max_value=10.0,
                format="%.2f"
                )
        else:
            stress_loss_ratio = None
    with colw:
        save_checkpoints = st.checkbox(
            "Save Checkpoints",
            help="Whether to save checkpoints during training. Default is False.  \n是否在训练过程中保存模型检查点，默认为False",
            value=False
        )
        if save_checkpoints:
            with st.expander("Checkpoint Interval"):
                ckpt_interval = st.number_input(
                "Checkpoint Interval (epochs)",
                help="Interval (in epochs) to save checkpoints. Default is 10.  \n保存模型检查点的间隔，单位为epoch，默认为10",
                value=10
                )
        else:
            ckpt_interval = None
        
    advanced = st.checkbox(
        "高级选项",
        help="Show advanced options for re-normalization and Weights & Biases logging.  \n显示重新归一化和Weights & Biases日志记录的高级选项",
        value=False
    )
    if advanced:
        re_normalize = st.checkbox(
        "Re-normalize Data",
        help="Whether to re-normalize energy and forces according to new data. Default is False.  \n是否根据新数据重新归一化能量和力，默认为False",
        value=False
        )
        if re_normalize:
            with st.expander("Normalization Factors"):
                scale_key = st.text_input(
                    "Key for scaling forces",
                    help="Key for scaling forces. Only used when re_normalize is True. Default is “per_species_forces_rms”.  \n用于缩放力的键值，仅在重新归一化时使用，默认为“per_species_forces_rms”",
                    value="per_species_forces_rms"
                )
                shift_key = st.text_input(
                    "Key for shifting energy",
                    help="Key for shifting energy. Only used when re_normalize is True. Default is “per_species_energy_mean_linear_reg”  \n用于平移能量的键值，仅在重新归一化时使用，默认为“per_species_energy_mean_linear_reg”",
                    value="per_species_energy_mean_linear_reg"
                )
                init_scale = st.text_input(
                    "Initial scale value",
                    help="Initial scale value. Only used when re_normalize is True. Default is None.  \n初始缩放值，仅在重新归一化时使用，默认为None",
                    value=""
                )
                init_shift = st.text_input(
                    "Initial shift value",
                    help="Initial shift value. Only used when re_normalize is True. Default is None.  \n初始平移值，仅在重新归一化时使用，默认为None",
                    value=""
                )
                trainable_scale = st.checkbox(
                    "Trainable Scale",
                    help="Whether the scale is trainable. Only used when re_normalize is True. Default is False.  \n缩放是否可训练，仅在重新归一化时使用，默认为False",
                value=False
                )
                trainable_shift = st.checkbox(
                    "Trainable Shift",
                    help="Whether the shift is trainable. Only used when re_normalize is True. Default is False.  \n平移是否可训练，仅在重新归一化时使用，默认为False",
                value=False
                )
        else:
            scale_key = None
            shift_key = None
            init_scale = None
            init_shift = None
            trainable_scale = False
            trainable_shift = False
                
        wandb = st.checkbox(
            "Use Weights & Biases",
            help="Whether to use Weights & Biases for logging. Default is False.  \n是否使用Weights & Biases进行日志记录，默认为False",
            value=False
        )
        if wandb:
            with st.expander("Weights & Biases API Key"):
                wandb_api_key = st.text_input(
                "Weights & Biases API Key",
                help="API key for Weights & Biases. Default is None.  \nWeights & Biases的API密钥，默认为None",
                value=None
                )
                wandb_project = st.text_input(
                "Weights & Biases Project Name",
                help="Project name for Weights & Biases. Default is “wandb_test”  \nWeights & Biases的项目名称，默认为“wandb_test”",
                value="wandb_test"
                )
        else:
            wandb_api_key = None
            wandb_project = None
    else:
        re_normalize = False
        scale_key = None
        shift_key = None
        init_scale = None
        init_shift = None
        trainable_scale = False
        trainable_shift = False
        wandb = False
        wandb_api_key = None
        wandb_project = None
    
    cmd = build_training_cmd(
    run_name=run_name,
    model=model,
    train_data=train_data,
    val_data=val_data,
    device=device,
    save_dir=save_dir,
    cutoff=cutoff,
    threebody_cutoff=threebody_cutoff,
    batch=batch,
    lr=lr,
    epochs=epochs,
    patience=patience,
    seed=seed,
    step_size=step_size,
    include_forces=include_forces,
    force_loss_ratio=force_loss_ratio,
    include_stresses=include_stresses,
    stress_loss_ratio=stress_loss_ratio,
    save_checkpoints=save_checkpoints,
    ckpt_interval=ckpt_interval,
    re_normalize=re_normalize,
    scale_key=scale_key,
    shift_key=shift_key,
    init_scale=init_scale,
    init_shift=init_shift,
    trainable_scale=trainable_scale,
    trainable_shift=trainable_shift,
    wandb=wandb,
    wandb_api_key=wandb_api_key,
    wandb_project=wandb_project,
    )   

    pretty_cmd = build_pretty_cmd(cmd)
    # 显示最终构建的训练命令
    with st.expander("查看训练命令"):
        st.code(pretty_cmd, language="bash")

    # 开始训练按钮
    if st.button("开始训练"):
        start_training(cmd, model)
