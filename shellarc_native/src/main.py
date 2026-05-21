import flet as ft
import os
import shutil
import json

from shellarc_core.auth.access_r2 import Cloudflare_R2_service_Access as AccessR2

APP_DATA_DIR = "/Users/shiinaayame/Downloads/TESTEST"

class ConfirmDialog:
    def show_dialog(self):
        pass

class MakeTable:
    def __init__(self, 
                 page: ft.Page
                 ) -> None:
        self.page = page

    def make_table(self,
                   table_data: dict
                   ) -> ft.DataTable:
        local_img_dir = os.path.join(APP_DATA_DIR, "img")
        table = ft.DataTable(
                    heading_row_height=50,
                    data_row_max_height=200,
                    data_row_min_height=200,
                    columns=[
                        ft.DataColumn(label=ft.Text("カット")),
                        ft.DataColumn(label=ft.Text("画面")),
                        ft.DataColumn(label=ft.Text("ト書き")),
                        ft.DataColumn(label=ft.Text("セリフ")),
                        ft.DataColumn(label=ft.Text("秒数")),
                    ],
                    rows = [
                        self.make_row(
                            cut_num=key,
                            src_img_path=os.path.join(local_img_dir, data["img"]),
                            script=data["script"],
                            monotlog=data["monolog"],
                            time_mark=data["time_mark"]
                        ) for key, data in table_data.items()
                    ],
                )
        return table

    def make_row(self,
                 cut_num: str,
                 src_img_path: str,
                 script: str,
                 monotlog: str,
                 time_mark: str
                 ) -> ft.DataRow:
        
        async def download_photo(e: ft.Event[ft.DataCell]):
            cell = e.control
            img_path = cell.data["path"]
            cut_num = cell.data["cut_num"]
            new_dir = await ft.FilePicker().get_directory_path()
            new_path = os.path.join(new_dir, os.path.basename(img_path))
            shutil.copy2(img_path, new_path)

        def edit_cell(e: ft.Event[ft.TextField]):
            cell = e.control
            cut_num = cell.data["cut_num"]
            item_key = cell.data["item_key"]
            new_value = e.control.value
            data_json = os.path.join(APP_DATA_DIR, "data.json")
            with open(data_json, "r", encoding="utf-8") as f:
                current_data = json.load(f)
            current_data[cut_num][item_key] = new_value
            with open(data_json, "w", encoding="utf-8") as f:
                json.dump(current_data, f, ensure_ascii=False, indent=3)

        row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(cut_num)),
                ft.DataCell(
                    ft.Image(
                        src=src_img_path,
                        width=300,
                        height=300,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    data={
                        "path" : src_img_path,
                        "cut_num" : cut_num
                        },
                    on_double_tap=download_photo,
                    disabled=self.page.web
                ),
                ft.DataCell(
                    ft.TextField(
                        value=script,
                        border=ft.InputBorder.NONE,
                        data={
                            "cut_num" : cut_num,
                            "item_key" : "script"
                            },
                        on_blur=edit_cell,
                        multiline=True
                    )
                ),
                ft.DataCell(
                    ft.TextField(
                        value=monotlog,
                        border=ft.InputBorder.NONE,
                        data={
                            "cut_num" : cut_num,
                            "item_key" : "monolog"
                            },
                        on_blur=edit_cell,
                        multiline=True
                    )
                ),
                ft.DataCell(
                    ft.TextField(
                        value=time_mark,
                        border=ft.InputBorder.NONE,
                        data={
                            "cut_num" : cut_num,
                            "item_key" : "time_mark"
                            },
                        on_blur=edit_cell,
                        multiline=True
                    )
                ),
            ]
        )
        return row




class MainTableArea:
    def __init__(self, 
                 page: ft.Page
                 ) -> None:
        self.page = page
        
    def make_table_area(self) -> ft.SafeArea:
        make_table = MakeTable(page=self.page)
        data_json = os.path.join(APP_DATA_DIR, "data.json")
        with open(data_json, "r", encoding="utf-8") as f:
            table_data = json.load(f)
        table = ft.SafeArea(
                    content=ft.ListView(
                        expand=True,
                        controls=[make_table.make_table(table_data=table_data)]
                    )
                )
        return table


def main(page: ft.Page):
    # 💡 ポイント3: 画面（ウインドウ）自体の高さが足りない場合に備えてスクロールを許可
    page.scroll = ft.ScrollMode.ADAPTIVE
    main_table_area = MainTableArea(page=page)
    main_layout = ft.Row(
        controls=[
            main_table_area.make_table_area()
        ]
    )

    main_table_area = MainTableArea(page)
    page.add(main_table_area.make_table_area())


if __name__ == "__main__":
    ft.app(target=main)