from pathlib import Path
import json
import datetime

import boto3

from shellarc_core.auth.access_r2 import Cloudflare_R2_service_Access as R2
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

def validate_paths() -> dict:
    local_backup_dir = Path(Cfg_IO().get_cfg_setting(Cfg_item.LOCAL_BACKUP))
    if not local_backup_dir.exists():
        print(f"{local_backup_dir} not exist")
        return
    backup_config_path = local_backup_dir / "backup_config.json"
    if backup_config_path.exists():
        with open(backup_config_path, "r", encoding="utf-8") as f:
            backup_config = json.load(f)
    else:
        backup_config = {
            "last_backup_time" : "0",
            "local_backup_dir" : str(local_backup_dir)
        }
    return backup_config

def backup_on_local() -> None:
    backup_config = validate_paths()
    if ("last_backup_time" not in backup_config or \
        "local_backup_dir" not in backup_config):
        print("Invalid backup config file")
        return
    last_backup_time = datetime.datetime.strptime(backup_config["last_backup_time"], "%Y%m%d%H%M%S")
    local_backup_dir = backup_config["local_backup_dir"]
    s3_client = R2().s3_client
    cfg_io = Cfg_IO()
    bucket = cfg_io.get_cfg_setting(Cfg_item.BUCKET_NAME)
    collection_name = cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)
    payload = {
        "Bucket": bucket,
        "Prefix" : f"{collection_name}/stage/"
    }
    obj_info_dict = {}
    for response in s3_client.get_paginator('list_objects_v2').paginate(**payload):
        obj_info_dict = response.get("Contents")
        for obj_info in obj_info_dict:
            obj_key = obj_info.get("Key")
            obj_name = obj_key.split("/")[-1]
            saved_timemark = datetime.datetime.strptime(obj_name.split("_")[-1].split(".")[0], "%Y%m%d%H%M%S")
            if saved_timemark <= last_backup_time:
                continue
            print(obj_key)
            s3_client.download_file(
                bucket,
                obj_key,
                f"{local_backup_dir}/{obj_name}"
            )
        current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_config["last_backup_time"] = current_datetime
        with open(Path(local_backup_dir) / "backup_config.json", "w", encoding="utf-8") as f:
            json.dump(backup_config, f, ensure_ascii=False, indent=2)
        print(f"Backup completed at {current_datetime}")
    

if __name__ == "__main__":
    backup_on_local()