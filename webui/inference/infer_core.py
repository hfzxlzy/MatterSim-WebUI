# 推理核心功能，含addons注册、加载模块
# 调用importlib和pkgutil动态加载addons模块，并注册其中的功能
import importlib
import pkgutil
import inference.addons as addons
# 加载addons模块并注册功能
from webui.inference.py_common import COMMON_HANDER, generate_common_setup
from webui.inference.py_structure import generate_structure_input

#插件基类
class ScriptModule:
    # 生成参数的唯一键，格式为 plugin_类名_参数名
    def param_key(self, name):
        return f"plugin_{self.__class__.__name__}_{name}"
    # 获取插件额外参数定义，返回一个字典
    def generate(self, state):
        raise NotImplementedError("插件必须实现 generate() 方法")
    
#预设插件注册表
SCRIPT_REGISTRY = {}

# 加载addons模块并注册功能
def load_addon_plugins():
    # 遍历addons目录下的所有模块
    for _, module_name, _ in pkgutil.iter_modules(addons.__path__):
        module = importlib.import_module(f"inference.addons.{module_name}")

        # 调用 register_plugin() 获取插件类
        if hasattr(module, "register_plugin"):
            # 调用模块中的注册函数，获取插件类
            PluginClass = module.register_plugin(ScriptModule)
            # 实例化插件并注入依赖
            plugin = PluginClass()
            # 注入公共组件为依赖
            plugin.COMMON_HANDER = COMMON_HANDER
            plugin.generate_common_setup = generate_common_setup
            plugin.generate_structure_input = generate_structure_input
            # 将插件注册到全局注册表，键为小写的类名（去掉 Script 后缀）
            plugin_name = PluginClass.__name__.replace("Script", "").lower()
            SCRIPT_REGISTRY[plugin_name] = plugin
            # 打印加载日志
            print(f"[Addons] Loaded plugin: {plugin_name}")

# 调用加载函数
load_addon_plugins()