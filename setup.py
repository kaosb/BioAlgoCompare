"""
Setup script para BioAlgoCompare
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bioalgocompare",
    version="2.0.0",
    author="BioAlgoCompare Team",
    description="Framework para algoritmos bio-inspirados aplicados a VRP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bioalgocompare",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "numpy>=1.20",
        "pandas>=1.3",
        "matplotlib>=3.4",
        "seaborn>=0.11",
        "scipy>=1.7",
        "tqdm>=4.62",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2",
            "pytest-cov>=2.12",
            "black>=21.6",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
        "dashboard": [
            "dash>=2.0",
            "plotly>=5.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "bioalgocompare=bioalgocompare:cli",
            "bioalgo=scripts.cli.analyze:main",
            "bioalgo-plugins=scripts.tools.manage_plugins:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
)