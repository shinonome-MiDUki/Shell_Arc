from notion_client import Client
from pathlib import Path

# Notion APIキーとデータベースIDを設定
notion_api_key = "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"
database_id = "36dd8177ad6f80b1b109d42432a37289"

notion = Client(auth=notion_api_key)

page_id = database_id

# アップロードしたい画像のパスを入力
image_path = Path("/Users/shiinaayame/Documents/Shell_Arc_discordbot/null_logo.png")
content_type = "image/png"

# ファイルのアップロードIDを作成
res_create = notion.file_uploads.create(
    mode="single_part",
    filename=image_path.name,
    content_type=content_type
)

# ファイルをアップロード
with open(image_path, "rb") as f:
    res_send = notion.file_uploads.send(
        file_upload_id = res_create["id"],
        file=(image_path.name, f, content_type)
    )

# ファイルをページに添付
res_append = notion.blocks.children.append(
    block_id=page_id,
    children=[{
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": res_send["id"]}
        }
    }]
)