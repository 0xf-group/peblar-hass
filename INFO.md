# Peblar EV charger component for Home Assistant

{% if pending_update %}

## New version is available

{% endif %}
{% if prerelease %}

### NB!: This is a Beta version!

{% endif %}

Custom component to support Peblar EV chargers.

The status sensor is the default sensor and has the following values

```
disconnected
awaiting_start
charging
ready_to_charge
completed
error
```

## Configuration

Configuration is done through in Configuration > Integrations where you first configure it and then set the options for what you want to monitor.
