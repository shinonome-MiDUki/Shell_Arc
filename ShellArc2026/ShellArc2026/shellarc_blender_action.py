import sys
import datetime
import os
import time
import pickle
from pathlib import Path

import bpy
import send2trash

class BlenderOperation:
    @classmethod
    def make_new_file(cls,
                      asset_name: str,
                      saving_dir: str
                      ) -> None:
        bpy.ops.wm.read_homefile(app_template='')
        default_coll = bpy.data.collections.get("Collection")
        default_coll.name = asset_name
        if not Path(saving_dir).exists():
            Path(saving_dir).mkdir(parents=True)
        bpy.ops.wm.save_as_mainfile(filepath=f"{saving_dir}/{asset_name}.blend")

    @classmethod
    def open_file(cls,
                  local_path: str
                  ) -> None:
        bpy.ops.wm.open_mainfile(filepath=local_path)

    @classmethod
    def save_file(cls) -> str:
        current_file_path = bpy.data.filepath
        bpy.ops.wm.save_as_mainfile()
        return current_file_path
    
    @classmethod
    def append_file(cls,
                    blend_file_path: str) -> None:
        if not Path(blend_file_path).exists:
            return
        inner_dir = os.path.join(blend_file_path, "Collection")
        with bpy.data.libraries.load(blend_file_path) as (data_src, data_dst):
            collection_names = data_src.collections
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
        for collection_name in collection_names:
            bpy.ops.wm.append(
                filepath=blend_file_path,
                directory=inner_dir,
                filename=collection_name,
                active_collection=True
            )
    
class LocalOperation:
    @classmethod
    def get_shellarc_cache_dir(cls,
                               info: str,
                               is_pathobj: bool=False
                               ) -> str:
        if sys.platform == "win32":
            freeze_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "ShellArc2026"
        elif sys.platform == "darwin":
            freeze_dir = Path.home() / "Library" / "Application Support" / "ShellArc2026"
        if info == "dir":
            rtn_path = freeze_dir
        elif info == "snapshot":
            rtn_path = freeze_dir / "snapshot"
        else:
            rtn_path = freeze_dir / info
        return rtn_path if is_pathobj else str(rtn_path)

    @classmethod
    def delete_snapshot_dir(cls,
                            ctx: bpy.context
                            ) -> None:
        if not "snapshot_path" in ctx.scene \
            or ctx.scene["snapshot_path"] == ""\
            or not Path(ctx.scene["snapshot_path"]).exists():
            return
        snapshot_path = ctx.scene["snapshot_path"]
        send2trash.send2trash(snapshot_path)
        ctx.scene["snapshot_path"] = ""

    @classmethod
    def snapshot_file(cls,
                      ctx: bpy.context
                      ) -> None:
        if not "snapshot_path" in ctx.scene \
            or ctx.scene["snapshot_path"] == ""\
            or not Path(ctx.scene["snapshot_path"]).exists():
            snapshot_dir = cls.get_shellarc_cache_dir(info="snapshot", is_pathobj=True)
            snapshot_dir.mkdir(exist_ok=True, parents=True)
            current_file_path = bpy.data.filepath
            snapshot_path = snapshot_dir / f"{Path(current_file_path).stem}_snapshot.blend"
            ctx.scene["snapshot_path"] = str(snapshot_path)
        snapshot_path = ctx.scene["snapshot_path"]
        bpy.ops.wm.save_as_mainfile(filepath=snapshot_path, 
                                    copy=True)

    @classmethod
    def shellarc_autosave(cls) -> float:
        cls.snapshot_file(ctx=bpy.context)
        return 300.0
    
    @classmethod
    def open_snapshot(cls,
                      ctx: bpy.context
                      ) -> None:
        if not "snapshot_path" in ctx.scene \
            or ctx.scene["snapshot_path"] == ""\
            or not Path(ctx.scene["snapshot_path"]).exists():
            return
        bpy.ops.wm.open_mainfile(filepath=ctx.scene["snapshot_path"])

    @classmethod
    def is_snapshot_exists(cls,
                           ctx: bpy.context,
                           asset_name: str
                           ) -> bool:
        snapshot_dir = cls.get_shellarc_cache_dir(info="snapshot", is_pathobj=True)
        snapshot_dir.mkdir(exist_ok=True, parents=True)
        snapshot_path = snapshot_dir / f"{asset_name}_snapshot.blend"
        if snapshot_path.exists():
            ctx.scene["snapshot_path"] = str(snapshot_path)
            return True
        return False
    
    @classmethod
    def get_freeze_dir_size(cls) -> int:
        freeze_dir = cls.get_shellarc_cache_dir(info="dir", is_pathobj=True)
        freeze_dir_size = sum(f.stat().st_size for f in freeze_dir.rglob('*') if f.is_file()) / (1024 * 1024)
        return int(freeze_dir_size)

    @classmethod
    def freeze_locally(cls,
                       ctx: bpy.context
                       ) -> None:
        freeze_dir = cls.get_shellarc_cache_dir(info="dir", is_pathobj=True)
        if not freeze_dir.exists():
            freeze_dir.mkdir(parents=True)
        current_file_path = Path(bpy.data.filepath)
        freeze_file_path = freeze_dir / f"{current_file_path.stem}_{datetime.datetime.now().strftime("%y%m%d%H%M%S")}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(freeze_file_path), 
                                    copy=True)
        ctx.scene.shellarc_prop_str_freezedirsize = f"{cls.get_freeze_dir_size()}MB"
        
    @classmethod
    def delete_freeze_dir(cls,
                          ctx: bpy.context
                          ) -> None:
        freeze_dir = cls.get_shellarc_cache_dir(info="dir", is_pathobj=False)
        preserve_latest = ctx.preferences.addons[__package__].preferences.preserve_latest_cache
        if not Path(freeze_dir).exists():
            return
        for f in os.listdir(freeze_dir):
            file_path = os.path.join(freeze_dir, f)
            if not os.path.isfile(file_path):
                continue
            file_time = os.stat(file_path).st_mtime
            if file_time < time.time() - preserve_latest:
                send2trash.send2trash(file_path)
        ctx.scene.shellarc_prop_str_freezedirsize = f"{cls.get_freeze_dir_size()}MB"
    
    @classmethod
    def get_frozen_files(cls) -> str:
        rtn_list = []
        asset_name = Path(bpy.data.filepath).stem
        freeze_dir = cls.get_shellarc_cache_dir(info="dir", is_pathobj=True)
        if freeze_dir.exists():
            frozen_list = os.listdir(str(freeze_dir))
            for f in frozen_list:
                if f.startswith(asset_name):
                    rtn_list.append(os.path.join(str(freeze_dir), f))
        if not rtn_list:
            return ""
        cache_path = Path(__file__).resolve().parent / "cache_reflogidx.pkl"
        with open(cache_path, "wb") as f:
            pickle.dump(rtn_list, f)
        return str(cache_path)
    
    @classmethod
    def open_frozen_file(cls,
                         ctx: bpy.context,
                         frozen_file_path: str
                         ) -> None:
        if not cls.get_shellarc_cache_dir(info="dir", is_pathobj=True).exists():
            return
        current_path = bpy.data.filepath
        cls.freeze_locally(ctx=ctx)
        bpy.ops.wm.open_mainfile(filepath=frozen_file_path)
        bpy.ops.wm.save_as_mainfile(filepath=current_path)
    