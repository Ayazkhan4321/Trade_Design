import os
import importlib

def load_plugins():
    plugins = []
    folder = "plugins"

    for file in os.listdir(folder):
        if file.endswith(".py"):
            module_name = f"{folder}.{file[:-3]}"
            module = importlib.import_module(module_name)

            if hasattr(module, "Plugin"):
                plugins.append(module.Plugin())

    return plugins