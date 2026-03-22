# rdce

[![CI Pipeline](https://github.com/valdal14/rdce/actions/workflows/ci.yml/badge.svg)](https://github.com/valdal14/rdce/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

Runtime Data Contract Enforcer: A lightweight Python 3 library for recursively validating and diffing nested JSON payloads against explicit schemas.

## Current Status
🚀 **Development Phase** 🚀
The core recursive validation engine is complete.

## Features
* **Recursive Type Validation:** Deeply inspects nested payloads.
* **Path Tracking:** Returns exact dot-notation breadcrumbs for schema drift (e.g., `user.metadata.age`).
* **Zero Dependencies:** The core engine is built purely on standard Python 3 capabilities.