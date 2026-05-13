class FileOperation:
    def __init__(self):
        pass

    def renamed(self, 
                proj_setting_data: dict, 
                working_index: int, 
                submitting_cut: int, 
                current_take: int
                ) -> str:
        """
        working_index, submitting_cut, current_take are 1-based index
        """
        naming_reference = []
        for i in range(0, proj_setting_data[f"component{working_index}"]["naming_section"]):
            process_subdata = proj_setting_data[f"component{working_index}"]
            naming_rule = process_subdata[f"name_component_{i+1}"]
            if naming_rule.startswith("-"):
                if naming_rule == "-cut":
                    naming_reference.append(f"cut{submitting_cut:02}")
                elif naming_rule == "-take":
                    naming_reference.append(f"take{current_take:02}")
            else:
                naming_reference.append(naming_rule)
        _renamed = "_".join(naming_reference)
        return _renamed
    
    def work_info(self, 
                  proj_setting_data: dict, 
                  processing_component: str
                  ) -> dict:
        component_number = int(proj_setting_data["component_number"])
        component_list = []
        component_list_eng = []
        for k in range(1,component_number+1):
            component_list.append(proj_setting_data[f"component{k}"]["display"])
            component_list_eng.append(proj_setting_data[f"component{k}"]["process"])

        working_index = component_list.index(processing_component) + 1
        working_component = component_list_eng[working_index-1]
        required_format = [proj_setting_data[f"component{working_index}"]["format"][0]]
        mime_format = [proj_setting_data[f"component{working_index}"]["format"][1]]
        _work_info = {
             "working_index" : working_index,
             "working_component" : working_component,
             "required_format" : required_format,
             "mime_format" : mime_format
        }
        return _work_info
    
    def update_database(self, 
                        current_take: int | None=None, 
                        work_data: dict=None, 
                        active: str | dict | None=None, 
                        temporary: str | dict | None=None, 
                        non_active: str | dict | None=None
                        ) -> dict:
        """
        This function is designed to prepare the structure of the data to be updated in the database when a cut is submitted
        which includes the current active take, temporary take, and non-active take

        Input var active, temporary and non_active can be either,
        a "clr" str for clearing command; or 
        a dictionary for updating info
        int var current_take is the current take number, it wont be updated when None
        
        The function returns a dictionary that can be directly used to update the database.
        The returned dictionary structure not a full copy of the database, so merge but not overwrite the existing database when updating.
        """
        structure = {}
        clr = {
            "naming": None, 
            "cut": None, 
            "take": None, 
            "creator": None, 
            "reviewer": None, 
            "comments": None
            }
        if current_take != None:
            structure["current_take"] = current_take
        if active != None:
            active = clr if active == "clr" else active
            structure["current_take"] = active
        if temporary != None:
            temporary = clr if temporary == "clr" else temporary
            structure["temporary"] = temporary
        if non_active != None and work_data != None:
            rejected_index = f"non_active_{non_active['take']:02}"
            structure[rejected_index] = non_active
            current_reject_count = int(work_data["current_reject_count"]) 
            structure["current_reject_count"] = current_reject_count + 1

        return structure
