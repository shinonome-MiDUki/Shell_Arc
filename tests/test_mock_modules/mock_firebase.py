from pathlib import Path
import json

class MockFirebase:
    @staticmethod
    def mock_update(cut_num: int,
                    component: str,
                    structure: dict
                    ) -> dict:
        mock_db_path = Path(__file__).resolve().parents[1] / "test_data/test_db.json"
        with open(mock_db_path, "r", encoding="utf-8") as f:
            mock_db = json.load(f)
        target_data = mock_db[f"cut{cut_num}"][component]
        for k, v in structure.items():
            target_data[k] = v
        return target_data
            
        