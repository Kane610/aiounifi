# aiounifi
Asynchronous library to communicate with Unifi Controller

## Network API v1

The `aiounifi/network/` package provides access to the official UniFi Network API (v1). It is available through `Controller.network` and is separate from the legacy REST interfaces under `aiounifi/interfaces/`.

### Structure

| Layer | Path | Responsibility |
|---|---|---|
| Entry point | `controller.network` | `ApiClient` instance, exposes all v1 interface slices |
| Connectivity | `network/v1/connectivity.py` | HTTP transport, error mapping, structured status handling |
| Interfaces | `network/v1/interfaces/` | Per-resource query methods (`sites`, `clients`) |
| Models | `network/v1/models/` | Typed request/response objects (`ApiRequest`, `ApiResponse`, `Site`, `Client`) |

### Usage

```python
# 1. Obtain the v1 API client from an initialised Controller
network = controller.network

# 2. Resolve and assign the active site UUID before calling site-scoped resources
#    Resolution order: configured UUID → legacy site resolver → v1 sites cache → fresh fetch
await network.assign_site(site="default")

# 3. List sites
sites = await network.sites.list()

# 4. List clients on the active site (first page, up to 25 results)
clients = await network.clients.list()

# Paginate and filter
guests = await network.clients.list_page(
    offset=0,
    limit=50,
    filter_value="access.type.eq('GUEST')",
)

# Fetch a single client by ID
client = await network.clients.get_details(client_id="<mac-or-id>")
```

## Acknowledgements
* Paulus Schoutsen (balloob) creator of aiohue which most of this code repository is modeled after.