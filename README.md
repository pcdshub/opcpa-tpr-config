# OPCPA TPR Configuration application for the LCLS NEH laser hall.

This application is for trigger configuration of the OPCPA laser systmes in
the NEH laser hall. The application is intended to provide information about
the current state of these systems, as well as provide controls for easy 
changes to repetition rate and "goose" triggering configuration.

There are two main ways to launch this pydm application:
1. Via the `./launch.sh` script, which selects a pre-installed environment
   and invokes the pydm command.
2. Via the `__main__.py` script, which can be bundled with the application
   for use in an installed python environment. You can execute this script
   by calling `opcpa_tpr_config`with the package installed, or by calling
   `python -m opcpa_tpr_config` from the root directory.
