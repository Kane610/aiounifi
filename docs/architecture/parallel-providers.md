# Parallel Providers

## Decision

aiounifi should treat the reverse-engineered API surface and the official UniFi API surface as long-lived peers.

The extended implementation is not a deprecated compatibility layer. It exposes details that the official API may never provide. The official implementation is not a replacement for that detail-rich surface. Downstream clients should be able to use both at the same time.

## Naming

- `extended`: reverse-engineered, broader and deeper controller coverage.
- `official`: documented UniFi API coverage.
- `composite`: orchestration layer that routes calls to one provider or combines results from both.

Avoid `legacy` naming because it implies eventual removal.

## Architectural Direction

The library should grow around three layers:

1. Provider implementations.
2. Canonical domain contracts shared by downstream users.
3. Composite routing and merge policy.

### Provider implementations

Each provider owns its transport, request/response modeling, and provider-specific raw objects.

Suggested top-level shape:

```text
aiounifi/
  providers/
    base.py
    extended/
    official/
    composite/
```

### Canonical domain contracts

Downstream code should not need to know raw provider differences for common operations.

For each domain area, define canonical capabilities such as:

- `clients.list`
- `clients.get`
- `devices.list`
- `devices.restart`
- `ports.list`
- `ports.set_poe_mode`

Providers may expose different subsets of those capabilities.

### Composite routing

Composite behavior needs an explicit routing policy per operation:

- `official`
- `extended`
- `prefer_official`
- `prefer_extended`
- `merge`

Read operations may support merge semantics. Write operations should resolve to a single provider.

## Requirements

### Must

- Keep the current implementation working unchanged.
- Add official support in parallel rather than by migration.
- Make provider capability support explicit and inspectable.
- Preserve strict typing and test coverage standards.

### Should

- Expose a runtime capability registry for downstream clients.
- Keep provider-specific raw models separate from canonical shared models.
- Document source-of-truth and merge policy per operation.

### Non-goals for the first PR

- No runtime behavior changes.
- No controller rewiring yet.
- No provider merge logic yet.
- No renaming of current interfaces or models.

## First PR Scope

The initial PR should only establish neutral scaffolding:

1. Provider namespaces.
2. Stable provider names and routing preferences.
3. A capability registry abstraction.
4. Tests proving routing semantics.

That gives later PRs a clean foundation for official and composite implementations without forcing premature structural moves.
