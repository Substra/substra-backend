import sys
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BASE_DIR.parent

sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "libs"))
