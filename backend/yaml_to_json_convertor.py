import yaml

class YamlJsonConvertor:
    def __init__(self, dict_from_yaml_data):
        self._meta_setting = {
            "project_name" : dict_from_yaml_data["project_name"],
            "collection_name" : dict_from_yaml_data["collection_name"],
            "mode" : dict_from_yaml_data["mode"],
            "cut_number" : dict_from_yaml_data["cut_number"],
            "component_number" : dict_from_yaml_data["component_number"],
            "parts" : dict_from_yaml_data["parts"],
            "spreadsheet_key" : dict_from_yaml_data["spreadsheet_key"]
                    }
        for i in range(1, int(dict_from_yaml_data["component_number"])+1):
            self._meta_setting[f"component{i}"] = dict_from_yaml_data["component"][i]

    @property
    def meta_setting(self):
        return self._meta_setting



    dict_from_yaml_data = yaml.safe_load(proj_setting_yaml)
