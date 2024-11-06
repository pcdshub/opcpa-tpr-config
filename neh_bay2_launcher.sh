#!/bin/bash
launcher="$(realpath $0)"
launcher_dir="$(dirname ${launcher})"

cd ${launcher_dir}

./launcher.sh opcpa_tpr_config/new_neh_bay2_config.yaml
