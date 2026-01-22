# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ocareport is a Python CLI tool that queries Oracle Cloud Infrastructure (OCI) to check compute resource availability across regions, availability domains, and fault domains. It uses the OCI Compute Capacity Report API to determine if specific shapes are available for provisioning.

## Commands

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run tests
```bash
pytest test_ocareport.py -v
```

### Run the tool
```bash
# Auto-detect authentication, check shape in home region
python ocareport.py -shape VM.Standard.E5.Flex

# Force config file authentication
python ocareport.py -auth cf -shape VM.GPU.A10.2

# Check all subscribed regions
python ocareport.py -shape VM.Standard.E5.Flex -region all

# Flex shape with specific resources
python ocareport.py -shape VM.Standard.E5.Flex -region eu-milan-1 -ocpus 24 -memory 512
```

## Architecture

### Project Structure
```
ocareport/
├── ocareport.py          # Main CLI entry point
├── modules/
│   ├── identity.py       # Authentication and OCI identity functions
│   └── utils.py          # Terminal colors and formatting helpers
└── test_ocareport.py     # Unit tests
```

### Authentication Flow
The tool tries authentication methods in order (unless `-auth` is specified):
1. **CloudShell** (`cs`): Uses OCI_CONFIG_FILE env var and delegation token
2. **Config File** (`cf`): Uses `~/.oci/config` or custom path
3. **Instance Principals** (`ip`): Uses VM identity via security token signer

### Key Functions

**ocareport.py**:
- `parse_arguments()`: CLI argument parsing
- `create_capacity_report()`: Calls OCI Compute Capacity Report API
- `main()`: Entry point, orchestrates auth → regions → query loop

**modules/identity.py**:
- `init_authentication()`: Auto-detects or uses specified auth method
- `authenticate_cloud_shell()`, `authenticate_config_file()`, `authenticate_instance_principals()`: Individual auth methods
- `get_region_subscription_list()`: Gets regions (home, specific, or all)
- `get_availability_domains()`, `get_fault_domains()`: Region topology discovery

### Program Flow
1. Parse arguments and initialize authentication
2. Get list of regions (home region, specific, or all subscribed)
3. For each region → for each AD → for each FD: query capacity report API
4. Display results in a Rich markdown table (green=AVAILABLE, red=unavailable)

## Dependencies

- `oci`: Oracle Cloud Infrastructure SDK for API calls
- `rich`: Terminal output formatting (tables, console)
- `pytest`: Testing framework
