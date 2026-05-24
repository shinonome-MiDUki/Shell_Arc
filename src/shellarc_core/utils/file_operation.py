import tempfile
import zipfile
import io
from pathlib import Path

from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

class FileOperation:
    @staticmethod
    def renamed(self, 
                cut_num: int,
                take: int,
                component: str, 
                ) -> str:
        cfg_io = Cfg_IO()
        name_section_num = cfg_io.get_cfg_setting(Cfg_item.COMPONENT, component, "naming_section")
        naming_ls = []
        for i in range(1, name_section_num + 1):
            naming_rule = cfg_io.get_cfg_setting(Cfg_item.COMPONENT, component, f"name_component_{i}")
            if naming_rule == "-cut":
                naming_ls.append(f"cut{cut_num}")
            elif naming_rule == "-take":
                naming_ls.append(f"take{take}")
            else:
                naming_ls.append(naming_rule.strip("-").strip())
        naming = "_".join(naming_ls)
        return naming

    @staticmethod
    def make_zip(files: dict[str, io.BytesIO]) -> str:
        tempzip_path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        try:
            with zipfile.ZipFile(tempzip_path.name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for name, byte_data in files.items():
                    zf.writestr(name, byte_data.getvalue())
            return tempzip_path.name
        except Exception as e:
            if Path(tempzip_path).exists():
                import os
                os.unlink(tempzip_path)
            print(f"make zip failed, error : {e}")
            return ""
                

