from setuptools import setup, find_packages

setup(
    name="bioalgocompare",
    version="1.0.0",
    description="Plataforma para evaluación estadística rigurosa de algoritmos bio-inspirados",
    author="BioAlgoCompare Team",
    author_email="contact@bioalgocompare.org",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "scipy>=1.7.0",
        "tqdm>=4.62.0",
        "click>=8.0.0",
        "seaborn>=0.11.0",
        "statsmodels>=0.13.0",
        "scikit-posthocs>=0.7.0",
        "jinja2>=3.0.0",
        "scikit-learn>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "bioalgo=scripts.analyze:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
