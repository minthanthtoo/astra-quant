# Security Policy

## Current execution boundary

Astra Quant is research and paper-trading software at this stage. Live order placement must not be implemented as an enabled default.

## Secrets

- Never commit credentials, API keys, private keys, or account data.
- Keep local secrets in environment variables or an approved secret manager.
- Use read-only exchange credentials for market-data ingestion.
- Do not grant withdrawal permissions to any exchange API key.
- Rotate any credential accidentally exposed in a commit immediately.

## AI boundary

AI-generated hypotheses, code, and configuration are untrusted inputs. They must not bypass deterministic risk checks, change execution permissions, or directly submit exchange orders.

## Reporting

Report suspected vulnerabilities privately to the repository owner. Do not publish exploitable details in public issues.
