# Shell Arc - プロジェクト管理プラットフォーム - 技術ドキュメント

## 目次
1. [API設定](#api設定)
2. [データサービスの初期設定](#データサービスの初期設定)
3. [プロジェクト設定](#プロジェクト設定)
4. [環境構築](#環境構築)
5. [ソースコード解説](#ソースコード解説)
6. [カスタマイズガイド](#カスタマイズガイド)
> ⚠️ システムの設定方法と利用方法は、本ドキュメントの第1〜3節で記載されています。\
> 第4−6節は、環境構築およびソースコードの詳しい解説ですので、システム本体をカスタム・改造したい場合のみご参照ください。

---

## API設定

### 概要
本プラットフォームは以下のAPIを使用しています：
- **boto3 Python API** - R2ストレージ
- **Firebase Python API** - データベース
- **oauth2client Python API** - GCP認証
- **gspread** - スプレッドシート操作
- **discord.py API** - Discordボット操作

### API　記載ファイルの場所
**以下に従って、APIキー情報記載用ファイルを作成してください。Streamlit Community Cloud以外のサービスでアプリケーションをデプロイする場合、`secrets.toml`への記述は不要です**:\
**secrets.toml** : `プロジェクトルート/.streamlit/secrets.toml`\
**.env** : `プロジェクトルート/.env` 

> 🔒 **セキュリティ注意**: APIキー情報は極めてセンシティブです。必ず`secrets.toml`および/または`.env`に記述し、それ以外のどこにも平文で記述しないでください。\
> また、`secrets.toml`の内容は、Streamlit Community Cloudでデプロイする際、Streamlit Community CloudのUI上で記述するものです\
> Githubへのコミットを含め、あらゆるプラットフォームでの公開をお避けください

> ⚠️ **重要**: プロジェクトをGitHubにコミットする際、必ず`.gitignore`ファイルを作成し、その中に`.streamlit/secrets.toml`と`.env`を記述した上で、コミットしてください。\
> これは、GitHubに「`secrets.toml`と`.env`は秘密だから公開しないでください」という指示を意味します。

### .streamlitフォルダと.env環境変数ファイルの表示方法
- **MacOS**: `Command` + `Shift` + `.`
- **Windows**: 「表示」タブ → 「表示」 → 「隠しファイル」

#### secrets.tomlへの記述方法

JSONファイルの構文を変換：
```
元: {"xxx": "yyy", "aaa": "bbb"}
↓
変換後:
xxx = "yyy"
aaa = "bbb"
```

#### .envへの記述方法
JSONファイルの構文を変換：
```
元: {"xxx": "yyy", "aaa": "bbb"}
↓
変換後:
xxx = yyy
aaa = bbb
```

---

### 1. GCP（Google Cloud Platform）認証情報の取得

#### 手順

1. [Google Cloud Platform](https://console.cloud.google.com/)にアクセスし、Googleアカウントでログイン
2. コンソールから新規プロジェクトを作成
3. **APIとサービス** → **ライブラリ** → **Google Sheet API**を検索し有効化
4. **APIとサービス** → **認証情報** → **認証情報を作成** → **サービスアカウントを作成**
5. 作成されたサービスアカウントの**メール**をクリック
6. **鍵** → **キーを追加** → **新しい鍵を作成** → **JSON** → **作成**
7. ダウンロードされたJSONファイルを開く

**secrets.toml**の`[GCP]`セクションに貼り付け：
```toml
[GCP]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

**.env**ファイルに貼り付け：
```env  
GCP_type = service_account
GCP_project_id = your-project-id
GCP_private_key_id = your-private-key-id
GCP_private_key = -----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n
GCP_client_email = your-service-account@project.iam.gserviceaccount.com
GCP_client_id = 123456789
GCP_auth_uri = https://accounts.google.com/o/oauth2/auth
GCP_token_uri = https://oauth2.googleapis.com/token
GCP_auth_provider_x509_cert_url = https://www.googleapis.com/oauth2/v1/certs
GCP_client_x509_cert_url = https://www.googleapis.com/robot/v1/metadata/x509/...
GCP_universe_domain = googleapis.com
``` 

---

### 2. Cloudflare R2認証情報の取得

#### 手順

1. [Cloudflare](https://www.cloudflare.com/)にアクセスし、アカウント作成またはログイン
2. Dashboardにアクセス
3. **Build** → **R2 object storage** → **Overview** → **Account Details** → **Manage** → **Create Account API token**
4. 指示に従ってAPI認証情報を取得

#### secrets.tomlへの記述
```toml
[CloudflareR2]
access_key_id = "your-access-key-id"
secret_access_key = "your-secret-access-key"
jurisdiction_specific_endpoints = "https://your-account-id.r2.cloudflarestorage.com"
```

#### .envへの記述
```env      
CloudflareR2_access_key_id = your-access-key-id
CloudflareR2_secret_access_key = your-secret-access-key
CloudflareR2_jurisdiction_specific_endpoints = https://your-account-id.r2.cloudflarestorage.com
```

---

### 3. その他の設定項目
#### secrets.tomlへの記述
```toml
[init]
collection_name = "your-collection-name"

[super]
id = "admin-password"
checker_id = "reviewer-password"
```

#### secrets.tomlへの記述
```env
init_collection_name = your-collection-name
super_id = admin-password
super_CHECKER_id = reviewer-password
```

---

### secrets.tomlの使い方
Streamlit Community Cloudでデプロイする際、UIで「高度」タプを開いて、当該箇所に上記にように記述したsecrets.tomlの内容をコピー&ヘイストしてください。

### .envの使い方
GitHubなどの外部プラットフォームでデプロイする際、当該プラットフォームの環境変数設定画面に上記にように記述した.envの内容をコピー&ヘイストしてください。

---

## データサービスの初期設定

新しい認証情報で以下のサービスを設定してください。

### Firebase

#### 手順

1. [Firebase](https://firebase.google.com/)にアクセスし、GCPと同じアカウントでログイン
2. コンソールから**新しいFirebaseプロジェクトを作成**
3. プロジェクト内で**アプリを追加**し、指示に従ってアプリ情報を登録
4. **プロダクトカテゴリ** → **構築** → **Firestore Database**をクリック
5. データベースを作成
6. コレクションを作成（名前は`secrets.toml`の`[init]`セクションに記述）

---

### Google Sheets

#### 手順

1. [Google Sheets](https://sheets.google.com/)で新規スプレッドシートを作成
2. `secrets.toml`の`[GCP]`セクションから`client_email`をコピー
3. スプレッドシートを`client_email`と共有し、**編集権限**を付与
4. スプレッドシートのURLからキーを取得

**URLの形式**:
```
https://docs.google.com/spreadsheets/d/【キー】/edit?gid=0#gid=0
```

---

### Cloudflare R2

#### 手順

1. [Cloudflare](https://www.cloudflare.com/)にアクセスし、ログイン
2. Dashboardにアクセス
3. **Build** → **R2 object storage** → **Overview** → **Create bucket**
4. バケットを作成

> ⚠️ **重要**: バケット名は必ずプロジェクト名と同じにしてください。

---

## プロジェクト設定

### project_setting.yamlについて

プロジェクト新規作成時、全ての情報を`project_setting.yaml`に記述します。

> ⚠️ **警告**: 
> - このファイルは**プロジェクト初期化専用**です
> - アップロードのたびにデータベースが**完全に初期化**されます
> - 既存データが削除されるため、初期化以外では絶対に実行しないでください
> - システム安定性のため、新項目の追加や既存項目の削除は行わないでください

---

### project_setting.yamlの記述方法
```yaml
# プロジェクト基本情報
project_name: プロジェクトの名称
mode: cut_base  # ← そのままにしてください
cut_number: 総カット数
component_number: 作業工程（原画、中割りなど）の数

# パート分け
parts:
  パート1名: [始まりのカット数, 終わりのカット数]
  パート2名: [始まりのカット数, 終わりのカット数]
  # パート名（A1、A2など）は自由に設定可能

# 作業工程の定義
component:
  1:
    process: プログラム内部で使う名前  # 必ず英文
    display: UIで表示される名前  # 日本語推奨
    naming_section: 命名の構成部分の数  # 例: "cut01_take02_genga" → 3
    name_component_1: -cut  # -cutと-takeは動的に番号付け
    name_component_2: -take
    name_component_3: "genga"
    # naming_sectionの数だけname_componentを定義
    format: [ファイル形式, MIME形式]  # 例: ["png", "image/png"]
    progress: 0  # 進捗状況の初期値
  2:
    # 同様に定義
  # component_numberの数だけ定義

# スプレッドシート書式（デフォルトスプレッドシート使用時は変更不要）
spreadsheet_format:
  row_before_cut_1: カット1のすぐ上の行番号
  progress_data_n_lines_under_last_cut: 最後の行の下のn行目
  component_info_range: 各作業工程が占める列数  # 例: 担当者と状態で2列
  
  # 作業工程に関係ない列の位置
  common_column:
    part: 2      # 列番号（A=1, B=2, ...）
    cut: 3
    difficulty: 4
    # ⚠️ この項目名はプログラム基幹に関わるため変更非推奨
  
  # 各作業工程の情報列の位置（作業工程の左端を0とする）
  component_info_column_structure:
    member: 0
    situation: 1
    progress: 0  # ← そのままにしてください
    # ⚠️ この項目名はプログラム基幹に関わるため変更非推奨
```

---

### プロジェクト初期化の実行

1. `project_setting.yaml`をsubmittingポータルにアップロード
2. スプレッドシートキーを入力（上記「Google Sheets」セクション参照）
3. データベースとスプレッドシートが自動生成されます

---

## これからは、ソースコードとそのカスタム化方法について解説します。PythonおよびAPI運用の基礎知識があることを前提としています。


## 環境構築

### 必要なツール
- Conda
- PIP
- Python 3.11.14

### セットアップ手順

**Conda をインストールしていない場合、[公式サイト](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html)からインストールしてから、お進みください。**

```bash
# 1. Python 3.11の仮想環境を作成
conda create -n 任意の環境名 python=3.11.14

# 2. 仮想環境を有効化
conda activate 先指定した環境名

# 3. 依存ライブラリをインストール（conda installは使用しないこと）
pip install streamlit firebase-admin gspread oauth2client boto3 PyYAML platformdirs discord.py python-dotenv
```

> ⚠️ **重要**: システム安定性のため、必ずpip installを使用してください。conda installは使用しないでください。

### ローカルで実行・デバッグする方法
```bash
# Conda 仮想環境を有効化
conda activate 先指定した環境名
# プロジェクトルートディレクトリに移動
cd プロジェクトルートディレクトリ
# Streamlit アプリケーションの起動
streamlit run 実行したいファイル.py
# また、Discordボットを起動する場合
python3 discord_connection.py
```

---

## ソースコード解説

### 命名規則の理解

プロジェクトで使用される命名パターン：

#### Firebase関連
| 名前パターン | 説明 | 例 |
|------------|------|-----|
| `ref_xxx_obj` | データベースのオブジェクト | `ref_setting_obj` |
| `ref_xxx` | `ref_xxx_obj.get()`の結果（参照点） | `ref_setting` |
| `xxx_data` | `ref_xxx.to_dict()`の結果（辞書データ） | `proj_setting_data` |

#### C1loudflare R2関連
Cloudflare R2関連のモジュールとクラスは、"Cloudflare_R2"または"R2"を名前に含みます。
ただし、そのクライエント参照は`s3_client`と命名されます。
これは、boto3のS3クライアントAPIを使用してR2にアクセスすることを強調するためです。

#### 作業工程関連
| 用語 | 説明 |
|------|------|
| `component` | 各作業工程全般を指す |
| `work` | 現在処理中の工程を指す |

---

### ファイル別解説

#### 1. access_database.py
**役割**: Firestore Databaseへのアクセス
```python
class AccessDB:
    def __init__(self):
        # データベースへ認証情報を提供し、アクセスを取得
    
    @property
    def database(self):
        # データベースへの参照を返す
```

---

#### 2. access_r2.py
**役割**: Cloudflare R2ストレージへのアクセスし、アップロード・ダウンロードを実行
```python
class Claoudflare_R2_service_Access:
    def __init__(self):
        # R2へ認証情報を提供し、バケットへのアクセスを取得
    
    @property
    def rs3_client(self):
        # R2クライアントへの参照を返す
```

---

#### 3. access_spreadsheet.py
**役割**: Google Sheetsスプレッドシートへのアクセス
```python
class AccessSpreadSheet:
    def __init__(self, spreadsheet_key):
        # Google Sheetsへ認証情報を提供し、アクセスを取得
    
    @property
    def spreadsheet_obj(self):
        # スプレッドシートへの参照を返す
```

---

#### 4. request_r2.py
**役割**: R2ストレージへのアクセスとファイルの取得・アップロード
```python
class Cloudflare_R2_service:
    def __init__(self, s3_client):
        # R2クライアントを受け取り、バケットへのアクセスを初期化
    
    def upload_file(self, uploaded_file, file_path):
        # UIからアップロードされたファイルをR2の正しい場所に保存
    
    def download_file(self, file_naming, to_download_file, download_destination):
        # 指定ファイルを取得し、ローカルにダウンロード
```

---

#### 5. load_spread_sheet.py
**役割**: スプレッドシート情報の取得・書き込み・更新
```python
class LoadSpreadSheet:
    def __init__(self, spreadsheet_format_data):
        # project_setting.yamlのspreadsheet_formatを取得
        # アクセスアルゴリズムを標準化
    
    def cell_id(self, column_index, row_index):
        # 行と列の番号を"A1"形式のセル名に変換
        # 例: (1, 1) → "A1"
    
    def column_index_of_requested_component_info(self, component_index, requesting_info):
        # 問い合わせ情報の該当列数を返す
    
    def load_spreadsheet(self, spreadsheet, cut_index, target_info, 
                         update_info=None, component_index=0):
        # 情報の取得と更新
        # update_info=None → 取得（問い合わせ）
        # update_info指定 → 書き込み
    
    def load_progress(self, spreadsheet, component_index, is_get, total_cut_number):
        # 進捗の取得と更新
        # is_get=True → 進捗を0-1の小数文字列で返す
        # is_get=False → 進捗を単純計算で更新
```

---
#### 6. discord_connection.py
**役割**: Discordボットの接続とメッセージ送信
```python
async def submit_file(message, submitting_person, submitting_cut, submitting_component, submission_raw):
    # Discord経由でファイルを提出する

async def push_action(message, submitting_cut, submitting_component):
    # Discord経由で提出（プッシュ）するときの挙動

async def on_message(message):
    # メッセージ受信を監視し、提出コマンドを処理
```

---

#### 7. project_setting.py
**役割**: プロジェクトの初期設定を実行

> ⚠️ **注意**: プロジェクト新規作成時に**一度のみ**実行
```python
def generate_meta(dict_from_yaml_data, collection_name, spreadsheet_key):
    # データベースのsettingドキュメントに格納する情報を生成
    # 辞書として返す

def generate_spreadsheet_format(dict_from_yaml_data):
    # データベースのspreadsheet_formatドキュメントに格納する情報を生成
    # 辞書として返す

def build_main_proj_db(db, dict_from_yaml_data, proj_collection, spreadsheet_key):
    # データベース自体の作成と構築

def build_main_proj_spread_sheet(spreadsheet, dict_from_yaml_data, proj_collection):
    # スプレッドシート自体の作成と構築

def main():
    # UIの定義とプログラムフローの制御
```

---

#### 8. file_operation.py
**役割**: ファイルの命名とデータベースの更新を一元管理
```python
class FileOperation:
    def __init__(self):
        pass
    
    def renamed(self, proj_setting_data, working_index, submitting_cut, current_take):
        # ファイル命名規則に基づき、正しいファイル名を生成して返す
    
    def work_info(self, proj_setting_data, processing_component):
        # 作業工程情報を処理して返す

 　　def update_database(self, current_take=None, work_data=None, active=None, temporary=None, non_active=None):
        # データベースの更新を実行
        # Noneの時、当該項目は更新されない
        # 各引数は辞書形式で渡す
        # non_activeが更新されるたび、current_reject_countも更新される
```

---

#### 9. common_initialisation.py
**役割**: 提出・取得・レビュー機能が共通使用するロジックと変数の一元管理

**提供される共通変数**:
- データベースのオブジェクト、参照、辞書
- スプレッドシートへの参照
- LoadSpreadSheetクラスのインスタンス参照
- 作業工程のインデックス、英文名、ファイル形式、MIME形式

**プロパティメソッド**:
提出・取得・レビュー用コードで使用される変数と同名のプロパティメソッドが定義されています。
```python
class CommonInitialisation:
    def __init__(self):
        # 共通変数の初期化
    
    @property
    def ref_setting_obj(self):
        # プロジェクト設定データオブジェクト
    
    @property
    def ref_setting(self):
        # プロジェクト設定データ参照
    
    @property
    def proj_setting_data(self):
        # プロジェクト設定データ辞書
    
    @property
    def ref_collection(self):
        # プロジェクトメインデータ参照
    
    @property
    def spreadsheet(self):
        # スプレッドシート参照
    
    @property
    def loadGS(self):
        # LoadSpreadSheetインスタンス参照
```

---

#### 10. submission.py
**役割**: ファイルの提出

UIとロジック定義を行います。

---

#### 11. requesting.py
**役割**: ファイルの取得

UIとロジック定義を行います。

---

#### 12. reviewer.py
**役割**: ファイルのレビュー

UIとロジック定義を行います。

---

## カスタマイズガイド

### 設計原則

1. **処理ロジックとUI操作**: `requesting.py`, `reviewer.py`, `submission.py`で行う
2. **外部データサービスの認証とクライアント参照へのアクセス**: `access_database.py`, `access_spreadsheet.py`, `access_r2.py`で行う・また上記3ファイルはUIコードから隠蔽
3. **初期設定制御**: `project_setting.py`は他のコードとの独立性を維持
4. **スプレッドシート操作**: `load_spread_sheet.py`を介して行う
5. **ストレージとのやり取り**: `request_r2.py`を介して行う
6. **命名操作とデータベース更新**: `file_operation.py`を介して行う
7. **共通ロジックと変数**: `common_initialisation.py`に集約

---

### ケース1: project_setting.yamlに項目を追加（spreadsheet_format以外）

#### 手順

**ステップ1**: `project_setting.yaml`に項目追加
```yaml
new_setting: 新しい値
```

**ステップ2**: `project_setting.py`の`generate_meta()`メソッドを編集
```python
def generate_meta(dict_from_yaml_data, collection_name, spreadsheet_key):
    meta_info = {
        "project_name": dict_from_yaml_data["project_name"],
        # ... 既存の項目 ...
        "new_setting": dict_from_yaml_data["new_setting"]  # ← 追加
    }
    return meta_info
```

**ステップ3**: データの使用
```python
# requesting.py, reviewer.py, submission.pyで使用可能
value = proj_setting_data["new_setting"]

# その他の場所では
value = common.proj_setting_data["new_setting"]
```

---

### ケース2: spreadsheet_formatの変更

#### 手順

**ステップ1**: `project_setting.yaml`の`spreadsheet_format`を編集
```yaml
spreadsheet_format:
  common_column:
    part: 2
    cut: 3
    difficulty: 4
    new_column: 5  # ← 追加
  
  component_info_column_structure:
    member: 0
    situation: 1
    new_info: 2  # ← 追加
```

**ステップ2**: 新しい情報にアクセス
```python
# load_spread_sheet.pyのLoadSpreadSheetクラスのメソッドを使用
loadGS.load_spreadsheet(
    spreadsheet=spreadsheet,
    cut_index=1,
    target_info="new_column",  # または "new_info"
    component_index=0  # common_columnの場合は0
)
```

---

### ケース3: 新しい機能の追加

#### ガイドライン

- **UIロジックを変更する場合**: `pages`フォルダに新しい`.py`ファイルを作成し、UIとロジックを定義
- **新しいデータサービスを追加する場合**: `backend`フォルダの新しい`access_新サービス名.py`を作成し、認証とクライアント参照を管理（必要に応じて`common_initialisation.py`にプロパティメソッドを追加・`request_サービス名.py`/`load_サービス名.py`系ファイルも作成）
- **新しいバックエンドロジックを追加する場合**: `backend`フォルダに新しい`.py`ファイルを作成し、ロジックを定義
- **新しいDiscordボットを追加する場合**: `discord_connection.py`にメソッドを追加・あるいは`discord_bot`フォルダに新しい`.py`ファイルを作成
- **データベース構造を変更する場合**: `project_setting.yaml`を編集し、それに応じて`project_setting.py`の`build_main_proj_db()`を編集
- **共通処理追加の場合**: `common_initialisation.py`にプロパティメソッドを追加（必要に応じて__init__に必要な変数も追加）
- **新しいファイル処理が必要な場合**: `file_operation.py`にメソッドを追加
- **スプレッドシート操作する場合**: 必ず`load_spread_sheet.py`を介して行う

#### バックエンドモジュールの使用
必要なモジュールをインポートする。ただしUIが定義されているスクリプトには、`access_database.py`, `access_spreadsheet.py`, `access_r2.py`をインポートしないでください

**`pages`または`discord_bot`フォルダからの使用:**
```python
project_root = os.path.dirname(os.path.abspath(__file__)) 
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.モジュールファイル名 import クラス名 as エイリアス名
# 例: from backend.request_r2 import Cloudflare_R2_service as R2
```

**`backend`フォルダ内のモジュールからの使用:**
```python
from .モジュールファイル名 import クラス名 as エイリアス名
# 例: from .access_r2 import Cloudflare_R2_service_Access as R2Access
```

---

### ケース4: 認証情報の更新

管理者が変更になった場合：

1. **GCP認証情報を再取得** → [API設定](#api設定)参照
2. **Cloudflare R2認証情報を再取得** → [API設定](#api設定)参照
3. **`secrets.toml`を更新**
4. **各サービスの共有設定を更新** → [データサービスの初期設定](#データサービスの初期設定)参照

---

## トラブルシューティング

### よくある問題

#### 問題1: データベース接続エラー

**原因**:
- `secrets.toml`の`[GCP]`セクションが正しく設定されていない
- Firebaseプロジェクトが作成されていない

**解決策**:
1. `secrets.toml`の認証情報を確認
2. Firebaseコンソールでプロジェクトとデータベースが存在するか確認

---

#### 問題2: スプレッドシートアクセスエラー

**原因**:
- スプレッドシートが`client_email`と共有されていない
- スプレッドシートキーが間違っている

**解決策**:
1. `secrets.toml`の`client_email`を確認
2. Google Sheetsの共有設定で`client_email`に編集権限があるか確認
3. URLからキーを正しく取得できているか確認

---

#### 問題3: R2ストレージアクセスエラー

**原因**:
- バケット名がプロジェクト名と一致していない
- API認証情報が間違っている

**解決策**:
1. Cloudflare R2のバケット名を確認
2. `secrets.toml`の`[CloudflareR2]`セクションを確認
3. `request_r2.py`の`R2_BUCKET`変数がプロジェクト名と一致するか確認

---

#### 問題4: プロジェクト初期化が失敗する

**原因**:
- `project_setting.yaml`の形式が間違っている
- スプレッドシートキーが無効

**解決策**:
1. YAMLの構文エラーをチェック（インデントなど）
2. 必須項目が全て記述されているか確認
3. スプレッドシートキーを再確認

---

### 推奨開発環境

- **IDE**: Visual Studio Code
- **Python**: 3.11.14
- **OS**: MacOS, Windows, Linux

---

### 関連リンク

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Firebase Documentation](https://firebase.google.com/docs)
- [gspread](https://docs.gspread.org/en/latest/)
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [discord.py Documentation](https://discordpy.readthedocs.io/ja/latest/api.html#)

---

## バージョン履歴

| バージョン | 変更内容 |
|-----------|----------|
| 2.0 | バックエンドのStreamlitへの依存性解消およびDiscord対応 |

---

## ライセンス

本システムは、Apache License 2.0ライセンスに基づいて配布されています。

---

**Document Version**: 2.0  
**Last Updated**: 2025
