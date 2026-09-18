#!/bin/bash
script_dir="$(dirname "$(realpath "$0")")"
project_root="${script_dir}/../.."

cd "${project_root}"

./launcher.sh opcpa_tpr_config/tests/test_gui.yaml
