#!/bin/bash
launcher="$(realpath $0)"
launcher_dir="$(dirname ${launcher})"

cd ${launcher_dir}

./new_launcher.sh opcpa_tpr_config/new_neh_bay3_config.yaml
