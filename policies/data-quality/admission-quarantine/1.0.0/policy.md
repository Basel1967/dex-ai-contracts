# Admission and Quarantine Policy v1.0.0

Stored means bytes and audit metadata were retained. Verified means schema, identifiers, time, lineage, classification and integrity passed. Available means verified and eligible. Quarantined means stored but ineligible. Rejected is reserved for unsafe or unparseable input; rejection still creates an audit record and retains safe raw evidence.

Closed quarantine reasons are in the schema. Invalid IDs/time/order, integrity problems, missing or unavailable mandatory raw evidence, unclassified data, unsupported versions, cross-environment references and invalid lineage force `available_at=null`. Duplicate, late and out-of-order alone do not quarantine. Unsupported versions fail closed.

Release requires a new append-only audit decision recording reason resolved, evidence, actor, time and validator/policy versions. In this single-owner development project Basel Atta owns release authority. A quarantined event is never mutated: emit a corrected or superseding event. Revocation appends an event and never deletes history.

