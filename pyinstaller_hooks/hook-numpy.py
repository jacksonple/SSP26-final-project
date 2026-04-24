from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata

module_collection_mode = "pyz+py"
warn_on_missing_hiddenimports = False

datas = collect_data_files(
    "numpy",
    excludes=[
        "**/*.py",
        "**/*.pyi",
        "**/__pycache__/*",
        "**/tests/*",
    ],
)

try:
    datas += copy_metadata("numpy")
except Exception:
    pass

binaries = collect_dynamic_libs("numpy")

hiddenimports = [
    "numpy._core",
    "numpy._core._exceptions",
    "numpy._core._multiarray_umath",
    "numpy.linalg",
    "numpy.random",
    "numpy.random._pickle",
]
