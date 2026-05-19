#!/usr/bin/env python3
"""Setup script for BizClippy — Your AI Business Assistant"""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bizclippy",
    version="1.0.0",
    author="BizClippy Team",
    description="AI-powered business assistant with a Clippy personality — powered by NVIDIA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bizclippy",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Business",
        "Topic :: Office/Business :: Scheduling",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
        "requests>=2.28.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        "console_scripts": [
            "bizclippy=bizclippy.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
