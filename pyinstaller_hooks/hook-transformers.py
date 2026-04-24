from PyInstaller.utils.hooks import collect_data_files, copy_metadata

module_collection_mode = "pyz+py"
warn_on_missing_hiddenimports = False

datas = collect_data_files(
    "transformers",
    includes=["**/*.json", "**/*.model", "**/*.txt", "**/*.tiktoken"],
    excludes=["**/__pycache__/*", "**/tests/*"],
)

for package_name in (
    "transformers",
    "tokenizers",
    "sentencepiece",
    "safetensors",
    "accelerate",
    "huggingface-hub",
):
    try:
        datas += copy_metadata(package_name)
    except Exception:
        pass

hiddenimports = [
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
]

excludedimports = [
    "jax",
    "librosa",
    "onnxruntime",
    "tensorflow",
    "torchvision",
]
