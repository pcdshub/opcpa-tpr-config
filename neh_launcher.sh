#!/bin/bash



launcher="$(realpath $0)"
launcher_dir="$(dirname ${launcher})"

cd ${launcher_dir}

./launcher.sh opcpa_tpr_config/neh_config.yaml &
