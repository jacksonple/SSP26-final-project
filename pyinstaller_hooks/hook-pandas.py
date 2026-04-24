from PyInstaller.utils.hooks import (
    check_requirement,
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)

module_collection_mode = "pyz+py"
warn_on_missing_hiddenimports = False

datas = collect_data_files(
    "pandas",
    excludes=[
        "**/*.py",
        "**/*.pyi",
        "**/__pycache__/*",
        "**/tests/*",
    ],
)

try:
    datas += copy_metadata("pandas")
except Exception:
    pass

binaries = collect_dynamic_libs("pandas")

hiddenimports = collect_submodules("pandas._libs")

if check_requirement("pandas >= 1.2.0"):
    hiddenimports += ["cmath"]
