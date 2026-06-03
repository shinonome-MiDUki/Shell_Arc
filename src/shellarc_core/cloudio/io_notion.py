from pathlib import Path

import requests

from shellarc_core.auth.access_notion import Notion_Access
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from shellarc_core.exception.structure_error import SA_CommunicationError, SA_ErrorCode

class Notion_IO:
    def __init__(self,
                 cut_num: int
                 ):
        notion = Notion_Access().get_notion_client
        database_id = str(Cfg_IO().get_cfg_setting(Cfg_item.NOTION_DBID))
        data_source_id = notion.databases.retrieve(database_id)['data_sources'][0]['id']
        self.notion_db = notion.data_sources.query(data_source_id = data_source_id)
        self.cut_num = cut_num

    def get_image_file(self,
                       download_destination: str | Path,
                       attr_name: str="画像"
                       ) -> None:
        if isinstance(download_destination, Path):
            download_destination = str(download_destination)
        image_url = self.notion_db["results"][self.cut_num - 1]["properties"][attr_name]["files"]["file"]["url"]
        response = requests.get(image_url)
        if response.status_code != 200:
            raise SA_CommunicationError(
                error_log="Request failed when getting image from an image url on Notion",
                error_code=SA_ErrorCode.SA_3000
            )
        with open(download_destination, "wb") as f:
            f.write(response.content)
