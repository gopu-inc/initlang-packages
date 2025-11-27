from setuptools import setup

setup(
    name="initpkg",
    version="1.0.0",
    py_modules=["initpkg"],
    entry_points={
        "console_scripts": [
            "initl=initpkg:main",
        ],
    },
    author="Mauricio",
    description="Package manager for INITLANG",
    python_requires=">=3.7",
)
