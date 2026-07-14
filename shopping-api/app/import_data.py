from .database import DEFAULT_CSV_PATH, database_path, import_csv


if __name__ == "__main__":
    changed = import_csv()
    print(f"Imported {changed} rows from {DEFAULT_CSV_PATH} into {database_path()}")

