import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

DATASET = "rohanrao/formula-1-world-championship-1950-2020"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
EXPECTED = ["circuits", "constructor_results", "constructor_standings", "constructors",
            "driver_standings", "drivers", "lap_times", "pit_stops", "qualifying", "races",
            "results", "seasons", "sprint_results", "status"]


def with_kagglehub():
    import kagglehub
    path = Path(kagglehub.dataset_download(DATASET))
    for name in EXPECTED:
        shutil.copy(path / f"{name}.csv", RAW / f"{name}.csv")


def with_cli():
    subprocess.run(["kaggle", "datasets", "download", "-d", DATASET, "-p", str(RAW)], check=True)
    archive = next(RAW.glob("*.zip"))
    with zipfile.ZipFile(archive) as z:
        z.extractall(RAW)
    archive.unlink()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for method in (with_kagglehub, with_cli):
        try:
            method()
            break
        except Exception as e:  # try the next method
            print(f"{method.__name__} failed: {e}")
    else:
        sys.exit("Download failed. Download the zip by hand from Kaggle and unzip it into data/raw/.")
    missing = [n for n in EXPECTED if not (RAW / f"{n}.csv").exists()]
    if missing:
        sys.exit(f"Missing files: {missing}")
    for n in EXPECTED:
        with open(RAW / f"{n}.csv", encoding="utf-8") as f:
            lines = sum(1 for _ in f) - 1
        print(f"  {n + '.csv':<28} {lines:>8} rows")
    print("Raw data ready in data/raw/")


if __name__ == "__main__":
    main()
