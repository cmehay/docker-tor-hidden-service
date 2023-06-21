## Global options
[Global]

{% if (env.get('TOR_CONTROL_PORT', '')).startswith('unix:') %}
{% set _, unix_path = env['TOR_CONTROL_PORT'].split(':', 1) %}
{% elif ':' in env.get('TOR_CONTROL_PORT', '') %}
{% set host, port = env['TOR_CONTROL_PORT'].split(':', 1) %}
{% else %}
{% set host = env.get('TOR_CONTROL_PORT') %}
{% endif %}

control_ip = {{ host or '' }}

control_port = {{ port or 9051 }}

control_socket = {{ unix_path or '' }}

control_pass = {{ env.get('TOR_CONTROL_PASSWORD', '') }}

state_file = {{ env.get('VANGUARDS_STATE_FILE', '/run/tor/data/vanguards.state') }}


{% if 'VANGUARDS_EXTRA_OPTIONS' in env %}
{% set extra_conf = ConfigParser().read_string(env['VANGUARDS_EXTRA_OPTIONS']) %}
{% if 'Global' in extra_conf %}
{% for key, val in extra_conf['Global'].items() %}
{{key}} = {{val}}
{% endfor %}
{% set _ = extra_conf.pop('Global') %}
{% endif %}
{{ extra_conf.to_string() }}
{% endif %}

{#
## Example vanguards configuration file
#
# All values below are default values and won't appear in final config file
# Original here: https://github.com/mikeperry-tor/vanguards/blob/master/vanguards-example.conf
#
# Enable/disable active vanguard update of layer2 and layer3 guards
enable_vanguards = True

# Enable/disable the bandwidth side channel detection checks:
enable_bandguards = True

# Enable/disable circuit build timeout analysis (informational only):
enable_cbtverify = False

# Enable/disable checks on Rendezvous Point overuse attacks:
enable_rendguard = True

# Close circuits upon suspected attack conditions:
close_circuits = True

# If True, we write (or update/rotate) layer2 and layer3 vanguards in torrc,
# then exit. This option disables the bandguards and rendguard defenses.
one_shot_vanguards = False

# The current loglevel:
loglevel = NOTICE

# If specified, log to this file instead of stdout:
logfile =

## Vanguards: layer1, layer2, and layer3 rotation params.
[Vanguards]

# How long to keep our layer1 guard (0 means use Tor default):
layer1_lifetime_days = 0

# The maximum amount of time to keep a layer2 guard:
max_layer2_lifetime_hours = 1080

# The maximum amount of time to keep a layer3 guard:
max_layer3_lifetime_hours = 48

# The minimum amount of time to keep a layer2 guard:
min_layer2_lifetime_hours = 24

# The minimum amount of time to keep a layer3 guard:
min_layer3_lifetime_hours = 1

# The number of layer1 guards:
num_layer1_guards = 2

# The number of layer2 guards:
num_layer2_guards = 3

# The number of layer3 guards:
num_layer3_guards = 8


## Bandguards: Mechanisms to detect + mitigate bandwidth side channel attacks.
[Bandguards]

# Maximum number of hours to allow any circuit to remain open
# (set to 0 to disable):
circ_max_age_hours = 24

# Maximum amount of kilobytes that can be present in a hidden service
# descriptor before we close the circuit (set to 0 to disable):
circ_max_hsdesc_kilobytes = 30

# Total maximum megabytes on any circuit before we close it. Note that
# while HTTP GET can resume if this limit is hit, HTTP POST will not.
# This means that applications that require large data submission (eg
# SecureDrop or onionshare) should set this much higher
# (or set to 0 to disable):
circ_max_megabytes = 0

# Warn if we can't build or use circuits for this many seconds.
circ_max_disconnected_secs = 30

# Warn if we are disconnected from the Tor network for this many seconds.
conn_max_disconnected_secs = 15

## Rendguard: Monitors service-side Rendezvous Points to detect misuse/attack
[Rendguard]

# No relay should show up as a Rendezvous Point more often than this ratio
# multiplied by its bandwidth weight:
rend_use_max_use_to_bw_ratio = 5.0

# What is percent of the network weight is not in the consensus right now?
# Put another way, the max number of rend requests from relays not in the
# consensus is rend_use_max_use_to_bw_ratio times this churn rate.
rend_use_max_consensus_weight_churn = 1.0

# Close circuits where the Rendezvous Point appears too often. Note that an
# adversary can deliberately cause RP overuse in order to impact availability.
# If this is a concern, either set this to false, or raise the ratio
# parameter above.
rend_use_close_circuits_on_overuse = True

# Total number of circuits we need before we begin enforcing rendezvous point
# ratio limits:
rend_use_global_start_count = 1000

# Number of times a relay must be seen as a Rendezvous Point before applying
# ratio limits:
rend_use_relay_start_count = 100

# Divide all relay counts by two once the total circuit count hits this many:
rend_use_scale_at_count = 20000
#}
