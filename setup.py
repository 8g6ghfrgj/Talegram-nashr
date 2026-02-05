#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import sys
from pathlib import Path


# ================= PYTHON VERSION =================

if sys.version_info < (3, 10):
    sys.exit("❌ يتطلب Python 3.10 أو أحدث")


# ================= README =================

this_dir = Path(__file__).parent

readme_file = this_dir / "README.md"

long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")


# ================= REQUIREMENTS =================

INSTALL_REQUIRES = [
    "python-telegram-bot==20.7",
    "telethon==1.34.0",
]


# ================= SETUP =================

setup(

    name="telegram-auto-bot",
    version="1.0.0",

    description="Telegram Auto Publishing Bot",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="Bot Developer",
    license="MIT",

    python_requires=">=3.10",

    packages=find_packages(),

    install_requires=INSTALL_REQUIRES,

    include_package_data=True,

    zip_safe=False,

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Communications :: Chat",
    ],

)
