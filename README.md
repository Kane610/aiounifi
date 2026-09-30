# aiounifi
Asynchronous library to communicate with Unifi Controller

## Network API v1, with an API key

`Controller.network` is a client of the official UniFi Network Integration
API, the versioned API under `/proxy/network/integration/v1` on the console.
It authenticates with an API key made in the console under
*Network → Integrations*, and needs no user, password or login. On consoles
joined to a UniFi fabric that is the only option, as those cannot hold local
users. The legacy interfaces (`controller.clients`, `controller.devices`, ...)
are unchanged and still need a local user.

```python
config = Configuration(session, "10.0.0.1", port=443, api_key="...")
network = Controller(config).network

info = await network.get_info()  # {"applicationVersion": "10.6.106"}
await network.assign_site("default")  # short name, display name or UUID

await network.devices.update()  # every page, cached by MAC address
switch = network.devices["70:a7:41:65:c0:ce"]
switch = await network.devices.get_details(switch.device_id)  # adds ports and radios
stats = await network.devices.get_statistics(switch.device_id)
await network.devices.power_cycle_port(switch.device_id, port_idx=3)
await network.devices.restart(switch.device_id)

await network.clients.update()
client = await network.clients.get_by_mac("aa:bb:cc:dd:ee:ff")
await network.clients.authorize_guest_access(client.client_id, time_limit_minutes=60)
await network.clients.unauthorize_guest_access(client.client_id)
```

The v1 API has no websocket. `update()` fetches every page of a list and then
removes cached items the console no longer returns, signalling `DELETED`.
Clients are the exception: the console lists connected clients only, so one
that leaves stays cached, as in the legacy API, and signals `CHANGED`.
`network.clients.is_connected(mac)` and `network.clients.last_seen(mac)` tell
whether and when it was last listed.
Errors are `NetworkApiError` subclasses that also inherit the legacy types
(`Unauthorized`, `Forbidden`, ...) and carry the API's structured error fields.

Try it from the command line:

```sh
aiounifi 10.0.0.1 -p 443 -k <api-key>
```

## Acknowledgements
* Paulus Schoutsen (balloob) creator of aiohue which most of this code repository is modeled after.