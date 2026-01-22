# OCI Compute Capacity Report (ocareport)

**Check the availability of any compute shape across OCI regions!**

Easily find out which regions offer compute shapes like VM.Standard.E5.Flex, GPU shapes, or bare metal instances. The tool provides availability status down to the Fault Domain level.

**Version: 1.1.0**

## Output Status Meanings

- **AVAILABLE** - The capacity for the specified shape is currently available
- **HARDWARE_NOT_SUPPORTED** - The necessary hardware has not yet been deployed in this region
- **OUT_OF_HOST_CAPACITY** - Additional hardware is currently being deployed in this region

## Quick Start

```bash
pip install -r requirements.txt
python ocareport.py -shape VM.Standard.E5.Flex
```

## Table of Contents

- [How It Works](#how-it-works)
- [Authentication Methods](#authentication-methods)
- [Command Line Options](#command-line-options)
- [Usage Examples](#usage-examples)
- [Setup for Instance Principals](#setup-for-instance-principals)
- [Running Tests](#running-tests)
- [Common GPU Shapes](#common-gpu-shapes)

## How It Works

When no authentication method is specified, the tool **automatically** tries authentication methods in this order:

1. **CloudShell** - Uses delegation token (when running in OCI CloudShell)
2. **Config File** - Uses local `~/.oci/config` file
3. **Instance Principals** - Uses VM identity (when running on OCI compute)

If all methods fail, the tool prompts for a custom config file path.

## Authentication Methods

| Method | Flag | Description |
|--------|------|-------------|
| Auto-detect | (none) | Tries all methods automatically |
| CloudShell | `-auth cs` | Uses OCI CloudShell delegation token |
| Config File | `-auth cf` | Uses local OCI config file |
| Instance Principals | `-auth ip` | Uses OCI compute instance identity |

## Command Line Options

| Argument | Parameter | Description |
|----------|-----------|-------------|
| `-auth` | `cs`, `cf`, `ip` | Force specific authentication method |
| `-config_file` | path | Path to OCI config file (default: `~/.oci/config`) |
| `-profile` | name | Config file profile section (default: `DEFAULT`) |
| `-region` | region_name | Region to analyze, or `all` for all regions (default: home region) |
| `-shape` | shape_name | **Required.** Compute shape name to check |
| `-ocpus` | number | OCPU count for flex shapes (default: 1) |
| `-memory` | number | Memory in GB for flex shapes (default: 1) |

## Usage Examples

### Check shape in home region (auto-detect auth)
```bash
python ocareport.py -shape VM.Standard.E5.Flex
```

### Check GPU availability with config file auth
```bash
python ocareport.py -auth cf -shape VM.GPU.A10.2
```

### Check in a specific region
```bash
python ocareport.py -shape VM.Standard.E5.Flex -region eu-frankfurt-1
```

### Check all subscribed regions
```bash
python ocareport.py -shape VM.Standard.E5.Flex -region all
```

### Flex shape with specific OCPU and memory
```bash
python ocareport.py -shape VM.Standard.E5.Flex -ocpus 24 -memory 512
```

### Using custom config file and profile
```bash
python ocareport.py -auth cf -config_file ~/my-config -profile PROD -shape BM.GPU.H100.8
```

### Full example with all options
```bash
python ocareport.py \
  -auth cf \
  -config_file ~/.oci/config \
  -profile DEFAULT \
  -region eu-paris-1 \
  -shape VM.Standard.E5.Flex \
  -ocpus 16 \
  -memory 128
```

## Setup for Instance Principals

If running from an OCI compute instance, configure Instance Principals authentication:

### 1. Create a Dynamic Group

Create a Dynamic Group called `OCI_Scripting` with this matching rule:

```
ANY {instance.id = 'ocid1.instance.oc1.xxx.your_instance_ocid'}
```

### 2. Create a Policy

Create a policy in the root compartment:

```
allow dynamic-group 'YourDomain'/'OCI_Scripting' to read all-resources in tenancy
```

## Running Tests

```bash
pip install -r requirements.txt
pytest test_ocareport.py -v
```

## Common GPU Shapes

| Shape | GPU | Count |
|-------|-----|-------|
| `VM.GPU.A10.1` | NVIDIA A10 | 1 |
| `VM.GPU.A10.2` | NVIDIA A10 | 2 |
| `VM.GPU3.1` | NVIDIA V100 | 1 |
| `VM.GPU3.2` | NVIDIA V100 | 2 |
| `VM.GPU3.4` | NVIDIA V100 | 4 |
| `BM.GPU4.8` | NVIDIA A100 40GB | 8 |
| `BM.GPU.A100-v2.8` | NVIDIA A100 80GB | 8 |
| `BM.GPU.H100.8` | NVIDIA H100 | 8 |
| `BM.GPU.L40S.4` | NVIDIA L40S | 4 |

## Project Structure

```
ocareport/
├── ocareport.py          # Main CLI tool
├── modules/
│   ├── __init__.py
│   ├── identity.py       # Authentication and OCI identity functions
│   └── utils.py          # Terminal colors and formatting
├── test_ocareport.py     # Unit tests
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── CLAUDE.md             # AI assistant instructions
```

## Credits

Inspired by [OCI_ComputeCapacityReport](https://github.com/Olygo/OCI_ComputeCapacityReport) by Florian Bonneville.

## Contact

Enrico Pesce - [@LinkedIn](https://www.linkedin.com/in/enricopesce/) - [@Blog](https://www.enricopesce.it/)

Project Link: [https://github.com/enricopesce/ocareport](https://github.com/enricopesce/ocareport)
