---
title: DataGuard — Data Validation Framework
status: final
created: 2026-09-28
updated: 2026-09-28
---

# Product Brief: DataGuard — Data Validation Framework

## Executive Summary

Data pipelines fail silently. Counts drift, duplicates slip through, nulls reach downstream consumers, and reconciliation gaps go undetected until they surface as production incidents or wrong reports. Today, testers catch these issues manually — slow, inconsistent, and unscalable.

DataGuard is a standalone, config-driven validation framework that automates quality checks across ETL pipelines. Teams define rules in a config file; DataGuard connects to source and target systems, runs the checks, and writes structured results to an output store any dashboard can consume. No custom code required.

V1 goal: a single engineer onboards a new pipeline in under an hour and runs a full validation suite without manual intervention.

## The Problem

Testers validate ETL pipelines by hand — querying source and target separately, comparing counts, spot-checking nulls, eyeballing for duplicates. This works until it doesn't.

The cost:
- **Speed:** Manual checks bottleneck every release and load cycle.
- **Consistency:** Coverage depends on who is checking and how much time they have. Validations get skipped under pressure.
- **Repeatability:** No audit trail, no trend line, no visibility into whether quality is improving or degrading.
- **Coverage:** Edge cases — referential integrity breaks, partial loads, column-level null spikes — rarely surface until downstream consumers are affected.

The result is data quality that is opaque, fragile, and expensive to maintain.

## The Solution

Teams define validation rules in a YAML or JSON config file and run them against any supported source/target pair with a single command.

Workflow:
1. Engineer writes a config file with connection details and checks (count comparison, null threshold, duplicate detection, referential integrity, reconciliation totals).
2. DataGuard runs — via CLI or triggered from a pipeline orchestrator.
3. DataGuard connects to source and target, executes checks, and writes structured results (pass/fail, actual vs. expected values, row counts, timestamps) to a results store.
4. Results are available in whatever dashboard the team already uses.

Validation that took hours of manual work runs in minutes, every time, with a full audit trail.

## What Makes This Different

Existing tools carry meaningful friction:

- **Great Expectations** — powerful but Python-heavy, with steep setup overhead.
- **Soda Core** — similar intent but leans toward cloud-managed SaaS and schema-aware profiling.
- **dbt tests** — tightly coupled to dbt projects; not usable outside that ecosystem.
- **Apache Deequ** — JVM/Spark-native; overkill for teams not already on Spark.

DataGuard's differentiators:
- **Config-driven:** No code required to define and run checks. Rules live in a file any engineer can read and edit.
- **Multi-source natively:** SQL, CSV, Parquet, JSON, Snowflake, and Databricks — cloud and on-prem — in one tool.
- **Lightweight:** Standalone, single deployment, no managed service dependency.
- **Output-agnostic:** Structured results go to a store; teams consume them in whatever observability stack they have.

The advantage is simplicity and breadth of connector support, not proprietary technology. [ASSUMPTION: No existing internal tooling is in use; if informal scripts exist, DataGuard should replace rather than co-exist with them.]

## Who This Serves

**Primary — Data engineers and QA/test engineers** running ETL pipelines across the org. They own the pipelines, define what "correct" looks like, and currently spend manual hours on validation. Success: onboard a new pipeline in under an hour, run checks on-demand or scheduled, stop doing this by hand.

**Secondary — Data consumers** (analysts, downstream teams) who benefit from fewer quality incidents and faster pipeline turnaround.

[ASSUMPTION: No dedicated data platform team manages a centralized catalog or observability layer. Teams adopt tooling independently.]

## Success Criteria

- A new team onboards a pipeline and runs a full validation suite in under 1 hour using only the documentation.
- All five check types (count, duplicate, null, reference, reconciliation) run correctly against at least two source/target system types.
- Results are written in a consistent, documented schema consumable by any standard BI tool.
- Zero manual intervention required between config definition and results output.
- [ASSUMPTION: At least 2 internal teams adopt within 30 days of release, as a usability proxy.]

## Scope — v1

**In:**
- Config-driven check definitions (YAML or JSON)
- Check types: row count comparison, duplicate detection, null/blank threshold, referential integrity, source-to-target reconciliation (aggregate totals)
- Connectors: SQL (JDBC/ODBC), CSV, Parquet, JSON, Snowflake, Databricks
- Cloud and on-prem execution
- Structured results output to a DB table or file
- CLI invocation
- Documentation sufficient for self-service onboarding

**Out of v1:**
- Native UI or dashboard — visualization is the consumer's concern
- Real-time or streaming validation — batch ETL only
- Auto-remediation or alerting — pass/fail output only
- ML-based anomaly detection
- Orchestrator-native integrations (Airflow plugins, Databricks Jobs SDK) — CLI is the entry point
- [ASSUMPTION: Schema drift detection and column-level profiling are out of v1 — flag if wrong.]

## Vision

When DataGuard works, teams treat data validation as a first-class part of every pipeline — not a manual QA step. Checks run on every load, results feed a shared observability layer, and quality becomes measurable over time.

In 2–3 years: a library of check types contributed across teams, orchestrator-native integrations, a central results store with cross-pipeline dashboards, and automated alerting. The v1 standalone tool is the proof point that earns that investment.
