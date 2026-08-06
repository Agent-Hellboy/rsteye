# hook-PIL.py

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all submodules and data files for PIL
hiddenimports = collect_submodules("PIL")
datas = collect_data_files("PIL")
