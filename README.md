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
  - \<title> : The title of the main screen
- \<lasers> : The laser system(s) to be supported
  - \<laser_name> : Laser system name
    - \<laser_desc> : Description of the laser system
    - \<tpr_base> : Base PV of the TPR for this laser system
    - \<channels> : TPR channels to be supported
      - \<ch name> : Name of TPR channel
        - \<desc> : Channel description
        - \<ch> : Channel number
        - \<show> : Boolean flag to display the trigger on the screen
    - \<rep_rates> : Mapping of rates to TPR Event codes
      - \<rate> : <event code> or <fixed rate code>
    - \<rate_configs> : Mapping of configuration buttons to channel config(s)
      - \<cfg_name> : Configuration name
        - \<rate> : Configuration description
        - \<ch> : Channel to configure. Maps to channel in \<lasers>/\<channels>
          - [ratemode] : Ratemode to configure. Accepts "Seq" or "Fixed".
          - [rate] : Rate to configure. Uses the <code> mapped by <rate> in \<rep_rates>.
          - [enable] : Enables/disables the channel. Accepts "Enabled" or
                       "Disabled".
          - [op] : Sets the trigger complementary logic. Accepts "NOOP",
                   "AND", and "OR".

Example configuration:

```
main:
    xpm_pv: "DAQ:TST:XPM:0:SEQCODES"
    title: "Example Rep. Rate Configuration"

lasers:
  laser_1:
    laser_desc: "Laser 1 TPR Configuration"
    tpr_base: "LAS:TST:TPR:01"

    channels:
      ch0:
        desc: "Channel 0"
        ch: "00"
        show: True
      ch1:
        desc: "Channel 1"
        ch: "01"
        show: True

    rep_rates:
      130: 256
      260: 257
      650: 258
      1300: 259

    rate_configs:
       cfg_130:
         rate: "130 Hz"
         ch0:
           ratemode: "Seq"
           rate: 130
           enable: "Enabled"
         ch1:
           ratemode: "Seq"
           rate: 130
           enable: "Enabled"

       cfg_260:
         rate: "260 Hz"
         ch0:
           ratemode: "Seq"
           rate: 260
           enable: "Enabled"
         ch1:
           ratemode: "Seq"
           rate: 260
           enable: "Enabled"

       cfg_CH0_AND:
         rate: "260 Hz CH0 AND"
         ch0:
           ratemode: "Seq"
           rate: 260
           enable: "Enabled"
           op: "AND"

       cfg_disable:
         rate: "CH0/1 Disable"
         ch0:
           enable: "Disabled"
         ch1:
           enable: "Disabled"
```
