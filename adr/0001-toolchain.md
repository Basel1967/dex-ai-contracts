# ADR-0001: Local contract toolchain

Status: Accepted locally / immutable base image still blocked by MSR-011

Use Python 3.12.13 standard library and GNU Make. The requested devcontainer base remains `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm`, but its placeholder digest is deliberately unchanged because Docker, registry inspection, build and scan tooling were unavailable. Floating-tag substitution is forbidden; publication remains fail-closed until the digest, build log and scan evidence are real.
