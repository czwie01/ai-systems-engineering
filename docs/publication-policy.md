# Publication policy

This repository is public by construction. Contributors must assume that every
committed byte and every collaboration surface is permanently public,
including Git history, commit messages, pull request descriptions, review
comments, test fixtures, generated artifacts, and CI logs.

The repository:

- uses only synthetic or explicitly redistributable material;
- never intentionally contains private AI transcripts;
- never contains employer or customer material;
- never contains excerpts copied from private repositories unless the material
  is independently redistributable and intentionally re-authored for this
  project;
- never contains credentials, tokens, production logs, or values that resemble
  live credentials.

Redaction is not a substitute for choosing safe source material. If provenance
or redistribution rights are uncertain, do not contribute the material.

## Pre-publication checklist

Before committing or opening a pull request, confirm:

- [ ] All examples, prompts, fixtures, and datasets are synthetic or have clear
      redistribution rights.
- [ ] No private names, employer/customer identifiers, personal data, private
      URLs, local absolute paths, or transcript remnants are present.
- [ ] No secret, token, credential, `.env` content, production log, or
      credential-like example value is present.
- [ ] Commit messages, branch-visible artifacts, and pull request text are safe
      for permanent public access.
- [ ] Claims match executable evidence and planned work is labeled `planned`.
- [ ] New third-party material includes its source and compatible license.
- [ ] CI failure output cannot disclose sensitive inputs or environment data.

If sensitive information is exposed, stop sharing it, rotate any affected
credential, and follow the security reporting process in
[SECURITY.md](../SECURITY.md).
