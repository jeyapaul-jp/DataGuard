---
title: DataGuard PRD — Addendum
created: 2026-09-28
updated: 2026-09-28
---

# DataGuard PRD Addendum

## Competitive Landscape

Context for positioning decisions in the PRD. Not a requirement — background for architecture and downstream consumers.

| Tool | Approach | Key friction |
|------|----------|-------------|
| **Great Expectations** | Python-native, profile-first | Steep learning curve, significant setup overhead, Python expertise required |
| **Soda Core** | Config-driven but SaaS-leaning | Cloud-managed orientation, schema-aware profiling setup required |
| **dbt tests** | Declarative tests in dbt project | Tightly coupled to dbt ecosystem; not portable outside it |
| **Apache Deequ** | Spark/JVM-native, programmatic | JVM dependency, Spark runtime required, overkill for non-Spark pipelines |

**DataGuard's gap:** None of the above are simultaneously config-driven (no code to define checks), multi-source natively (SQL + files + Snowflake + Databricks), and standalone (no SaaS dependency, no ecosystem lock-in). DataGuard's differentiator is simplicity and connector breadth — not proprietary technology. The moat is execution speed (1 week to v1) and frictionless onboarding.
