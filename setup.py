from setuptools import find_packages, setup

import versioneer

with open("requirements.txt", "rt") as fp:
    install_requires = [
        line for line in fp.read().splitlines()
        if line and not line.startswith("#")
    ]

setup(
    name="opcpa_tpr_config",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    license="BSD",
    author="SLAC National Accelerator Laboratory",
    packages=find_packages(),
    include_package_data=True,
    description="App description",
    install_requires=install_requires,
    entry_points={
        'gui_scripts': [
            'opcpa_tpr_config=opcpa_tpr_config.__main__:main'
        ]
    },
)
