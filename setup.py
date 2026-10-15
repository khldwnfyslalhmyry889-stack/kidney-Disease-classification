from pathlib import Path

import setuptools

ROOT = Path(__file__).resolve().parent
README = ROOT / 'README.md'

long_description = (
    README.read_text(encoding='utf-8')
    if README.is_file()
    else 'مشروع تصنيف صور الكلى إلى أربع فئات.'
)

setuptools.setup(
    name='cnnClassifier',
    version='1.0.0',
    description='Four-class kidney image classification',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=(
        'https://github.com/'
        'hamed77alotheeb/Kidney-Disease-Classification-MLOps-V2'
    ),
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    python_requires='>=3.8,<3.11',
)
