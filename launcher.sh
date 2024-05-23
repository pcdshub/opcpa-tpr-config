#!/bin/bash

# Uncomment and set to the latest version to freeze dependency
#export PCDS_CONDA_VER=5.8.0
#export PCDS_CONDA_VER=dev

source /cds/group/pcds/pyps/conda/pcds_conda
#source /cds/group/pcds/pyps/conda/dev_conda
export PYTHONPATH=/cds/group/pcds/pyps/apps/dev/pythonpath:$PYTHONPATH

if [[ $# -ne 1 ]]; then
    echo
    echo "Usage: launcher.sh <cfg file path>"
    echo
    exit 1
fi

launcher="$(realpath $0)"
launcher_dir="$(dirname ${launcher})"
app="${launcher_dir}/opcpa_tpr_config/opcpa_tpr_config.py"

cfg="$(realpath $1)"

pydm ${app} ${cfg}
