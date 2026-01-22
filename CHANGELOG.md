# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024

### Added
- Auto-detect authentication mode (tries CloudShell, Config File, Instance Principals in order)
- Modular project structure with separate `modules/` directory
- Comprehensive unit tests in `test_ocareport.py`
- Support for flexible OCPU and memory configuration with `-ocpus` and `-memory` flags
- Rich terminal output with color-coded availability status
- Documentation with usage examples and GPU shape reference

### Changed
- Refactored authentication logic into `modules/identity.py`
- Improved error handling for authentication failures
- Enhanced CLI argument parsing

## [1.0.0] - 2024

### Added
- Initial release
- Query OCI Compute Capacity Report API
- Support for CloudShell, Config File, and Instance Principals authentication
- Check shape availability across regions, availability domains, and fault domains
- Support for checking all subscribed regions with `-region all`
- Color-coded terminal output
