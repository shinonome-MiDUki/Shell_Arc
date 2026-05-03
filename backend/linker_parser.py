import yaml
import os

class LinkerParser:
    def __init__(self):
        pass

    def linker_file(self, path):
        if os.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                dict_from_yaml_data = yaml.safe_load(f)
            return dict_from_yaml_data
        
    def restructure_linker(self, linker_file_path = None, linker_dict = None):
        if linker_file_path is None and linker_dict is None:
            return
        if linker_dict is None:
            linker_dict = self.linker_file(linker_file_path)
        linker_dict_restructure = {
            "foward_ref": linker_dict,
            "backward_ref": {}
        }
        for k, v in linker_dict.items():
            for sub_v in v:
                linker_dict_restructure["backward_ref"][sub_v] = k
        return linker_dict_restructure
    
    def trace_to_parent(self, linker_dict_restructure, child):
        parent = linker_dict_restructure["backward_ref"].get(child)
        return parent
    
    def trace_to_child(self, linker_dict_restructure, parent):
        child = linker_dict_restructure["foward_ref"].get(parent)
        return child
