#!/bin/bash

# Uncomment and set to the latest version to freeze dependency
# export PCDS_CONDA_VER=5.1.1
source /cds/group/pcds/pyps/conda/pcds_conda

launcher="$(realpath $0)"
launcher_dir="$(dirname ${launcher})"
app="${launcher_dir}/appname/appname.py"

pydm ${app} $@ # Can add pydm args here
