import flet as ft
import flet_datatable2 as fdt

import os
import shutil
import json
import zipfile
import requests
import time
import base64
import mimetypes
from pathlib import Path

APP_DATA_DIR = os.getenv("FLET_APP_STORAGE_DATA")
APP_ASSET_DIR = str(Path(__file__).resolve().parent / "assets")
DATA_URL = "https://pub-2557eee0e2ed4d73bfa7813bfd90af80.r2.dev/storyboard/img.zip"

class ConfirmDialog:
    def show_dialog(self):
        pass

class MakeTable:
    def __init__(self, 
                 page: ft.Page,
                 main_table_area
                 ) -> None:
        self.page = page
        self.main_table_area = main_table_area

    def make_table(self,
                   table_data: dict,
                   is_launch: bool=True
                   ) -> ft.DataTable:
        table = fdt.DataTable2(
                    expand=True,
                    heading_row_height=50,
                    columns=[
                        fdt.DataColumn2(label=ft.Text("カット"), fixed_width=80),
                        fdt.DataColumn2(label=ft.Text("画面"), fixed_width=310),
                        fdt.DataColumn2(label=ft.Text("ト書き"), fixed_width=300),
                        fdt.DataColumn2(label=ft.Text("セリフ"), fixed_width=300),
                        fdt.DataColumn2(label=ft.Text("秒数"), fixed_width=150),
                        fdt.DataColumn2(label=ft.Text("更新"), fixed_width=80)
                    ],
                    rows = [
                        self.make_row(
                            cut_num=key,
                            src_img_name=data["img"],
                            script=data["script"],
                            monotlog=data["monolog"],
                            time_mark=data["time_mark"],
                            is_launch=is_launch
                        ) for key, data in table_data.items()
                    ],
                )
        return table

    def make_row(self,
                 cut_num: str,
                 src_img_name: str,
                 script: str,
                 monotlog: str,
                 time_mark: str,
                 is_launch: bool = True
                 ) -> ft.DataRow:
        
        def load_image_data_url(path: str) -> str:
            try:
                mime = mimetypes.guess_type(path)[0] or "image/png"
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime};base64,{b64}"
            except Exception:
                return ""
        
        async def download_photo(e: ft.Event[ft.DataCell]):
            cell = e.control
            img_path = cell.data["path"]
            cut_num = cell.data["cut_num"]
            new_dir = await ft.FilePicker().get_directory_path()
            if new_dir is None:
                return
            new_path = os.path.join(new_dir, os.path.basename(img_path))
            shutil.copy2(img_path, new_path)

        async def update_storyboard(e: ft.Event[ft.Button]):
            btn_control = e.control
            src_img_path = btn_control.data["img"]
            new_img_path_ls = await ft.FilePicker().pick_files(allow_multiple=False)
            if not new_img_path_ls:
                return
            new_img_path = new_img_path_ls[0].path
            shutil.copy2(new_img_path, src_img_path)
            self.main_table_area.render_table_area(is_launch=False)
            self.page.update()

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

        local_img_dir = os.path.join(APP_DATA_DIR, "img")
        src_img_path = os.path.join(local_img_dir, src_img_name)
        if os.path.exists(src_img_path):
            image_src = src_img_path if is_launch else load_image_data_url(src_img_path)
        else:
            image_src = os.path.join(APP_ASSET_DIR, "holder.png")
        row = fdt.DataRow2(
            specific_row_height=200,
            cells=[
                ft.DataCell(ft.Text(cut_num)),
                ft.DataCell(
                    ft.Image(
                        src=image_src,
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
                ft.DataCell(
                    ft.Button(
                        content="",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=update_storyboard,
                        data={
                            "img" : src_img_path
                        }
                    )
                )
            ]
        )
        return row



class MainTableArea:
    def __init__(self, 
                 page: ft.Page
                 ) -> None:
        self.page = page
        self.make_table = MakeTable(
            page=self.page,
            main_table_area=self
            )
        self.table_container_view = ft.ListView(expand=True)

    def make_table_area(self) -> ft.SafeArea:
        self.render_table_area()
        table = ft.SafeArea(content=self.table_container_view)
        return table
        
    def render_table_area(
            self,
            is_launch: bool=True
            ) -> None:
        data_json = os.path.join(APP_DATA_DIR, "data.json")
        if not os.path.exists(APP_DATA_DIR):
            os.makedirs(APP_DATA_DIR)
        if not os.path.exists(data_json):
            with open(data_json, "w", encoding="utf-8") as f:
                table_data = {}
                json.dump(table_data, f)
        else:
            with open(data_json, "r", encoding="utf-8") as f:
                table_data = json.load(f)
        self.table_container_view.controls = [
            self.make_table.make_table(
                table_data=table_data,
                is_launch=is_launch
                )
        ]


def download_storyboard():
    if not os.path.exists(APP_DATA_DIR):
        os.makedirs(APP_DATA_DIR)
    cache_dir = os.path.join(APP_DATA_DIR, "img")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    temp_cache = os.path.join(APP_DATA_DIR, "tempcache.zip")
    data_json = os.path.join(APP_DATA_DIR, "data.json")
    temp_data_json = os.path.join(cache_dir, "data.json")
    try:
        print("Requesting")
        response = requests.get(DATA_URL, stream=True)
        with open(temp_cache, "wb") as f:
            for ck in response.iter_content(chunk_size=8192):
                f.write(ck)
        with zipfile.ZipFile(temp_cache, "r") as zipf:
            zipf.extractall(APP_DATA_DIR)
        os.rename(temp_data_json, data_json)
        os.unlink(temp_cache)
    except:
        print("Requests failed")

def export_storyboard():
    pass


def main(page: ft.Page):
    print(APP_DATA_DIR)
    cache_dir = os.path.join(APP_DATA_DIR, "img")
    if not os.path.exists(APP_DATA_DIR) or not os.path.exists(cache_dir):
        download_storyboard()
    page.scroll = ft.ScrollMode.ADAPTIVE

    def fetch_storyboard():
        download_storyboard()
        main_table_area.render_table_area()
        page.update()

    page.floating_action_button = ft.Column(
        alignment=ft.MainAxisAlignment.END,
        controls=[
            ft.FloatingActionButton(
                key="fetch",
                icon=ft.Icons.DOWNLOAD,
                on_click=fetch_storyboard,
                bgcolor="7cf7ff"
            ),
            ft.FloatingActionButton(
                key="export",
                icon=ft.Icons.IMPORT_EXPORT,
                on_click=export_storyboard,
                bgcolor="7cf7ff"
            )
        ]
    )

    main_table_area = MainTableArea(page=page)
    main_layout = ft.Row(
        controls=[
            main_table_area.make_table_area()
        ]
    )

    page.add(main_table_area.make_table_area())

ft.run(main)