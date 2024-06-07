from setuptools import setup, find_packages

setup(
    name="font-sorting",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy==1.26.4",
        "pillow==10.3.0",
        "torch==2.3.0",
        "torchvision==0.18.0",
        "timm==1.0.3",
        "requests==2.32.3"
    ],
    python_requires='>=3.6',
    author="Matevž Kovačič",
    author_email="matevz.celje@gmail.com",
    description="A system for sorting fonts according to visual similarity.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/matevz-kovacic/font-sort",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
