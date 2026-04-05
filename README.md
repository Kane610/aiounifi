# aiounifi

Asynchronous library to communicate with Unifi Controller

## Architecture direction

The library is evolving toward parallel provider implementations instead of a replacement model.

- `extended` will represent the reverse-engineered controller surface.
- `official` will represent documented UniFi APIs.
- `composite` will route or merge both for downstream clients.

The initial foundation for that direction is documented in `docs/architecture/parallel-providers.md`.

## Acknowledgements

- Paulus Schoutsen (balloob) creator of aiohue which most of this code repository is modeled after.
