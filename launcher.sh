#!/bin/bash

# Uncomment and set to the latest version to freeze dependency
export PCDS_CONDA_VER=6.0.1
#export PCDS_CONDA_VER=dev

source /cds/group/pcds/pyps/conda/pcds_conda
# export PYTHONPATH=/cds/group/pcds/pyps/apps/dev/pythonpath:$PYTHONPATH
# export PYTHONPATH=/cds/home/t/tjohnson/trunk/forks/pydm:$PYTHONPATH
#export PYTHONPATH=/cds/home/opr/tmoopr/git/lcls2_051024/psdaq:$PYTHONPATH
export PYTHONPATH=/cds/home/opr/rixopr/git/lcls2_101824/psdaq:$PYTHONPATH

if [[ $# -ne 1 ]]; then
    echo
    echo "Usage: launcher.sh <cfg file path>"
    echo
    exit 1
fi

launcher="$(realpath $0)"
launcher_dir="$(dirname ${launcher})"
app="${launcher_dir}/opcpa_tpr_config/user_config.py"

cfg="$(realpath $1)"

python ${app} -c ${cfg} -d
