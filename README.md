# OPCPA TPR Configuration application for the LCLS NEH laser hall.

This application is for trigger configuration of the OPCPA laser systmes in
the NEH laser hall. The application is intended to provide information about
the current state of these systems, as well as provide controls for easy
changes to repetition rate and "goose" triggering configuration.

The application accepts a configuration file and generates a screen based on
the configuration.

There are two main ways to launch this pydm application:
1. Via the `./launch.sh` script, which selects a pre-installed environment
   and invokes the pydm command.
2. Via the `__main__.py` script, which can be bundled with the application
   for use in an installed python environment. You can execute this script
   by calling `opcpa_tpr_config`with the package installed, or by calling
   `python -m opcpa_tpr_config` from the root directory.

## Configuration File Structure

The configuration file takes the following \<required> and [optional] configuration keys:

- \<main> : configuration values for overall system/screen
  - \<xpm_pv> : PV of the XPM to be displayed and programmed
  - \<meta_pv> : PV of upstream AD metadata
  - \<engine1> : Engine number for laser on/off time event codes
  - \<engine2> : Engine number for laser base rate event codes
  - \<bay> : String describing the laser bay being used, e.g. "Bay 2"
  - \<laser_database> : Happi database json file to be used for this bay
  - \<title> : The title of the main screen
  - \<devices> : Devices to be supported by this system.
    - \<device> : Happi database name of device.
      - \<rbvs> : List of device attributes to show
      - \<show> : Boolean flag to display the device on the screen

- \<goose_arrival_configs> : Options for goose "arrival" control
    - \<config_name> : Name of arrival config
      - \<desc> : Config description
      - \<device> : Happi database name of device.
        - [config attr] : The configuration will accept any configuration attribute of the pcdsdevices device class, for example pcdsdevices.tpr.TprTrigger can have `seqcode`, `operation`, etc.

Example configuration:

```
main:
    xpm_pv: "DAQ:TST:XPM:0:SEQCODES"
    meta_pv: "TPG:SYS0:1:DST04"
    engine1: "0"
    engine2: "1"
    title: "Example Rep. Rate Configuration"
    bay: "Bay 0"

    laser_database: "neh_bay0_db.json"

    devices:
      trigger0:
        rbvs: ["name", "eventrate", "seqcode", "width_setpoint", "delay_setpoint"]
        show: True
      trigger0:
        rbvs: ["name", "eventrate", "seqcode", "width_setpoint", "delay_setpoint"]
        show: True
      scalar_pv1:
        rbvs: ["name", "val"]
        show: True
      scalar_pv2:
        rbvs: ["name", "val"]
        show: True

goose_arrival_configs:
    goose_off:
      desc: "Goose off"
      trigger0:
        ratemode: "Seq"
        enable_trg_cmd: "Disabled"
      trigger1:
        ratemode: "Seq"
        enable_trg_cmd: "Disabled"
      scalar_pv1:
        val: 0.0
      scalar_pv2:
        val: 0.0

    goose_early:
      desc: "Goose off"
      trigger0:
        ratemode: "Seq"
        enable_trg_cmd: "Enabled"
      trigger1:
        ratemode: "Seq"
        enable_trg_cmd: "Enabled"
      scalar_pv1:
        val: -1.0
      scalar_pv2:
        val: -1.0

    goose_late:
      desc: "Goose off"
      trigger0:
        ratemode: "Seq"
        enable_trg_cmd: "Enabled"
      trigger1:
        ratemode: "Seq"
        enable_trg_cmd: "Enabled"
      scalar_pv1:
        val: 1.0
      scalar_pv2:
        val: 1.0
```
