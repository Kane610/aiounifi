# aiounifi – Copilot Instructions

## Architecture: Two Independent API Trees

There are two completely separate API clients. Never mix their types.

| Tree | Entry point | Path | Purpose |
|---|---|---|---|
| Legacy REST | `Controller` | `aiounifi/interfaces/` | UniFi Controller REST API (stable, websocket-driven) |
| Network API v1 | `controller.network` (`ApiClient`) | `aiounifi/network/v1/` | Official UniFi Network API (paginated, site-scoped) |

`controller.network` is a `cached_property` — it is created on first access and shares the same `Configuration` as the legacy tree.

## Layer Contracts

| Layer | Path | Rule |
|---|---|---|
| Data models | `aiounifi/models/` | Pure data — TypedDicts, dataclasses, value objects. No I/O, no mutable state. |
| Legacy handlers | `aiounifi/interfaces/` | Subclass `APIHandler`. Wire to `controller.messages` via `process_messages`/`remove_messages`. |
| v1 handlers | `aiounifi/network/v1/interfaces/` | Subclass `network/v1/api_handlers.APIHandler`. Override `normalize_obj_id` to canonicalize storage keys. |
| v1 models | `aiounifi/network/v1/models/` | Typed request/response objects for the v1 API. |
| Cross-cutting | `aiounifi/subscription.py` | `SubscriptionHandler` mixin + `ItemEvent` enum. Shared by both handler trees. |
| Errors | `aiounifi/errors.py` | All exception types. `AiounifiException` is the base. |

## Key Extension Patterns

### Adding a new legacy endpoint
1. Create `aiounifi/models/<resource>.py` — TypedDict for the item, `@dataclass ApiRequest` subclass.
2. Create `aiounifi/interfaces/<resource>.py` — subclass `APIHandler[YourModel]`, set `obj_id_key`, `item_cls`, `api_request`.
3. Register it in `aiounifi/controller.py` (`self.<resource> = YourHandler(self)`).
4. Add the HTTP mock to `tests/conftest.py` `_mock_endpoints` fixture.
5. Add `<resource>_payload` fixture to `tests/conftest.py` defaulting to `[]`.

### Adding a new v1 endpoint
1. Create `aiounifi/network/v1/models/<resource>.py` — TypedDict + `@dataclass ApiRequest` (path must start with `/v1/`).
2. Create `aiounifi/network/v1/interfaces/<resource>.py` — subclass `network/v1/api_handlers.APIHandler[YourModel]`.
3. Export from `aiounifi/network/v1/interfaces/__init__.py` and `aiounifi/network/v1/__init__.py`.
4. Attach to `ApiClient.__init__` in `aiounifi/network/v1/api_client.py`.
5. Write tests under `tests/network/v1/`.

### `normalize_obj_id` hook (v1 handlers only)
Override in a handler subclass to canonicalize item storage keys before they are stored or looked up:
```python
def normalize_obj_id(self, obj_id: str) -> str:
    return normalize_mac(obj_id)  # e.g. Clients uses MAC as canonical key
```

### Subscription pattern
`SubscriptionHandler.subscribe(callback, event_filter, id_filter)` returns an `UnsubscribeType` callable.
- `event_filter`: single `ItemEvent` or tuple; `None` = all events.
- `id_filter`: specific object ID(s); `None` = all objects (wildcard `"*"`).

## Test Conventions

### Fixture injection protocol
Payload fixtures all default to `[]` (empty). Inject real data via `@pytest.mark.parametrize`:
```python
@pytest.mark.parametrize("wlan_payload", [WLANS])
@pytest.mark.usefixtures("_mock_endpoints")
async def test_wlans(unifi_controller):
    ...
```
`_mock_endpoints` reads the current value of every `*_payload` fixture and registers all HTTP mocks at once.

### v1 test fixtures (in `tests/network/v1/conftest.py`)
| Fixture | Returns | Usage |
|---|---|---|
| `network_client` | `ApiClient` | Standard v1 client backed by `unifi_controller` |
| `network_client_with_site` | `ApiClient` | Client with `_site_id = "site-uuid"` pre-assigned |
| `network_connectivity` | `Connectivity` | Direct connectivity unit tests |

### Request assertion helper
```python
from tests.helpers.request_assertions import assert_request_called_with
assert_request_called_with(mock_aioresponse, "put", "/api/s/default/...", json_body={...})
```

### Payload builder pattern (v1 tests)
Define a `_<resource>_payload(**overrides)` helper at the top of the test file that merges defaults with overrides, to keep test data DRY.

## Type Checking
- mypy strict: `disallow_untyped_defs`, `no_implicit_reexport`, `warn_return_any`, etc.
- All public symbols must be in `__all__` — `no_implicit_reexport = true` is enforced.
- `TYPE_CHECKING` guards are used for circular-import-safe type annotations.

## Pre-commit Workflow
1. `git add` your changes.
2. `git commit` → pre-commit runs ruff + ruff format + mypy automatically.
3. If ruff **modifies files**, the commit is aborted — re-stage the auto-fixed files and commit again.
4. mypy failures require manual fixes.

## Naming Conventions
- Request dataclasses: `<Resource>Request` with a `create(...)` classmethod.
- Response TypedDicts: `<Resource>Data` (raw API shape) + `<Resource>` (handler-facing wrapper if needed).
- Handler classes: `<Resources>` (plural) for collection handlers.
- Test fixtures: `<resource>_payload` for data, `test_<resource>_<scenario>` for tests.
