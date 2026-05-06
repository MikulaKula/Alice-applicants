from pathlib import Path

DOCS_DIR = Path("documents")
GOLD_PATH = Path("gold_dataset.json")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

COLLECTION_NAME = "hse_admission_docs"
DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150
TOP_K_LIST = [1, 3, 5]
