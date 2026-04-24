from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

module_collection_mode = "pyz+py"
warn_on_missing_hiddenimports = False

datas = collect_data_files(
    "torch",
    excludes=[
        "**/*.h",
        "**/*.hpp",
        "**/*.cpp",
        "**/*.cuh",
        "**/*.pyi",
        "**/include/*",
        "**/share/*",
        "**/test/*",
    ],
)
binaries = collect_dynamic_libs("torch")

hiddenimports = [
    "torch._C",
    "torch._VF",
    "torch.backends",
    "torch.backends.mps",
    "torch.distributed",
    "torch.distributions",
    "torch.fft",
    "torch.fx",
    "torch.jit",
    "torch.linalg",
    "torch.nn",
    "torch.nn.functional",
    "torch.optim",
    "torch.serialization",
    "torch.special",
    "torch.utils",
    "torch.utils.data",
]

excludedimports = [
    "caffe2",
    "functorch",
    "torch.testing._internal",
    "torchvision",
]
