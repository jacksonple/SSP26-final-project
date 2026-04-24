# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata


ROOT_DIR = Path(SPECPATH)
BUILD_MODE = os.environ.get("PYI_BUILD_MODE", "onefile").lower()


def _safe_copy_metadata(package_name):
    try:
        return copy_metadata(package_name)
    except Exception:
        return []


datas = []
for package_name in (
    "numpy",
    "pandas",
    "transformers",
    "torch",
    "tokenizers",
    "sentencepiece",
    "safetensors",
    "accelerate",
    "huggingface-hub",
):
    datas += _safe_copy_metadata(package_name)

datas += collect_data_files(
    "transformers",
    includes=["**/*.json", "**/*.model", "**/*.txt", "**/*.tiktoken"],
    excludes=["**/__pycache__/*", "**/tests/*"],
)
datas += collect_data_files("tokenizers")
datas += collect_data_files("sentencepiece")

binaries = []
binaries += collect_dynamic_libs("torch")
binaries += collect_dynamic_libs("tokenizers")
binaries += collect_dynamic_libs("sentencepiece")

hiddenimports = [
    "fitz",
    "numpy",
    "numpy._core",
    "numpy._core._exceptions",
    "numpy._core._multiarray_umath",
    "numpy.random",
    "pandas",
    "yaml",
    "safetensors",
    "sentencepiece",
    "tokenizers",
    "transformers.pipelines",
    "transformers.pipelines.text_generation",
    "transformers.generation.utils",
    "transformers.cache_utils",
    "transformers.modeling_utils",
    "transformers.models.auto.auto_factory",
    "transformers.models.auto.configuration_auto",
    "transformers.models.auto.modeling_auto",
    "transformers.models.auto.tokenization_auto",
    "transformers.models.gemma.configuration_gemma",
    "transformers.models.gemma.modeling_gemma",
    "transformers.models.gemma.tokenization_gemma",
    "transformers.models.gemma.tokenization_gemma_fast",
    "transformers.models.gemma3.configuration_gemma3",
    "transformers.models.gemma3.modeling_gemma3",
    "transformers.models.gemma3.processing_gemma3",
    "torch",
    "torch._C",
    "torch._VF",
    "torch.backends",
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

a = Analysis(
    ["pipeline.py"],
    pathex=[str(ROOT_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(ROOT_DIR / "pyinstaller_hooks")],
    hooksconfig={},
    runtime_hooks=[str(ROOT_DIR / "pyinstaller_hooks" / "runtime_env.py")],
    excludes=[
        "IPython",
        "matplotlib",
        "pytest",
        "tensorflow",
        "torchvision",
        "torchaudio",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if BUILD_MODE == "onedir":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="ssp_pipeline",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="ssp_pipeline",
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="ssp_pipeline",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
