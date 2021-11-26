from setuptools import find_packages, setup

with open("README.md", encoding='utf-8') as in_:
    setup(
        name='av-clipboard-lib',
        version='1.0.0',
        packages=find_packages(),
        url='https://github.com/DeltaEpsilon7787/av-clipboard-lib',
        license='MIT',
        author='DeltaEpsilon7787',
        author_email='deltaepsilon7787@gmail.com',
        long_description=in_.read(),
        long_description_content_type="text/markdown",
        description='Small ArrowVortex clipboard processing library',
        python_requires='>=3.6',
        install_requires=["attrs"],
    )
