#!/usr/bin/env python3
"""
Setup script for DEPONPM - NPM Dependency Checker Tool
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="deponpm",
    version="1.0.0",
    author="DEPONPM Team",
    author_email="",
    description="A tool to check package.json files for unclaimed or non-existent NPM dependencies",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/deponpm",
    py_modules=["deponpm"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "deponpm=deponpm:main",
        ],
    },
    keywords="npm, dependencies, package.json, checker, validation",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/deponpm/issues",
        "Source": "https://github.com/yourusername/deponpm",
    },
)
