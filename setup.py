from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("VERSION", "r") as f:
    version = f.read().strip()

setup(
    name="video-dedup",
    version=version,
    author="hnwxwt",
    author_email="",
    description="智能视频去重工具 - Smart Video Deduplication Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/video-dedup",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=[
        "opencv-python>=4.5.0",
        "Pillow>=8.0.0",
        "imagehash>=4.2.0",
        "send2trash>=1.8.0",
        "numpy>=1.19.0",
    ],
    entry_points={
        "console_scripts": [
            "video-dedup=main:main",
        ],
    },
)
