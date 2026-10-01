# Release notes

## Unreleased

- Run Python regression tests and the Molecule syntax scenario in the main CI
  quality gate.
- Run CodeQL on all pushed branches as well as pull requests targeting main.
- Document playbook and sanitizer proxy interfaces and link the Best Practices
  badge profile.

## Release policy

No non-draft release has been published at the time this file was introduced.
Development snapshots are identified by their Git commit SHA.

Published releases use unique `vMAJOR.MINOR.PATCH` tags and Semantic Versioning.
Release notes describe changes and known incompatibilities. Security fixes
identify the relevant public advisory or CVE after coordinated disclosure, and
state the affected and fixed versions. Do not publish details of an undisclosed
vulnerability in draft release notes. Published notes are available on the
[GitHub Releases page](https://github.com/kpeacocke/piclaw/releases).
