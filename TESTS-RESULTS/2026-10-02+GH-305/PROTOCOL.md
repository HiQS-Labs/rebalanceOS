# Focused local qualification protocol

Scope: Rebalance #282, umbrella pointer #305 and Forge #937. Core natural-capture/same-note/backup proof is separate from consumer qualification. No remote device enablement or full-fleet claim.

Decision: preserve old consumer and semantic IDs, use the already configured full-history compatibility export, and add source references to existing metadata. A new reader/store or primary-key migration is unnecessary. Canonical raw rows may exceed eligible filtered projection keys; count identities and explicit exclusions separately. Keep memory policy unchanged; a scheduled guard refusal is recorded as deferral.

Manual controls: synthetic Unicode LF framing; stable canonical Daily citation; idempotent source/origin preservation; union across origins sharing a filtered key; same-pass collision and reordered replay; cache fallback provenance; selected CLIO maintenance facade produces nonempty metadata without embedding. Controls use synthetic disposable sources only. Existing affected suites run in a separate disposable full clone. No added gate or suite registry.

Production decision rule: deploy source only after independent QA and focused/static gates. Destination backup must pass quick_check before named-source ingest; canonical capture source/history/header remain preserved. Selected CLIO metadata backfill must show nonempty canonical-reference coverage without new embeddings or cloud synthesis. A guard refusal means no runtime-qualified consumer refresh and remains pending, not a forced success. Never bypass the guard to satisfy this protocol.

Rollback: retain independently verified private destination/config/plist backups; stop destination writers before any restore and first preserve intervening updates. Source history is never restored backward. Other participants remain disabled. Seven-day soak and live multi-device recovery remain open.
