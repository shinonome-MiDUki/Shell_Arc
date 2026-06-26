SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$(dirname "$SCRIPT_DIR")"

echo "export SHELLARC_LOCAL_BACKUP=\"${BACKUP_DIR}\"" >> ~/.zshrc

VENV_DIR="${SCRIPT_DIR}/venv"
python3 -m venv "${VENV_DIR}"
${VENV_DIR}/bin/python3 -m pip install --upgrade pip
${VENV_DIR}/bin/python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt"

echo "alias nuru='${VENV_DIR}/bin/python3 ${SCRIPT_DIR}/backup_on_local.py'" >> ~/.zshrc

echo "設定を反映するには: source ~/.zshrc を実行してください"
echo "以降は、nuru コマンドでバックアップを実行できます"