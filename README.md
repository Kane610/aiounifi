# aiounifi
Asynchronous library to communicate with Unifi Controller

## Home Assistant integration guidance

The object-oriented network configuration endpoint is not available on all
UniFi Network versions. The Home Assistant integration should catch
`EndpointNotFound` for this nonessential coordinator, stop retrying it, and
report one concise compatibility message while leaving the rest of the
integration available.

Required endpoints and write operations should continue to surface
`EndpointNotFound` instead of treating 404 responses as empty data.

## Acknowledgements
* Paulus Schoutsen (balloob) creator of aiohue which most of this code repository is modeled after.