# OCI Compute Capacity Report (ocareport)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OCI SDK](https://img.shields.io/badge/OCI%20SDK-2.149.0+-orange.svg)](https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/)
[![Tests](https://github.com/enricopesce/ocareport/actions/workflows/ci.yml/badge.svg)](https://github.com/enricopesce/ocareport/actions/workflows/ci.yml)

**Check Oracle Cloud Infrastructure compute shape availability across all regions instantly.**

A command-line tool that queries the OCI Compute Capacity Report API to find available compute resources including VMs, bare metal instances, and GPU shapes (NVIDIA A100, H100, A10, L40S) across regions, availability domains, and fault domains.

## Features

- **Multi-Region Support** - Check capacity in your home region, a specific region, or all subscribed regions at once
- **Flexible Authentication** - Auto-detects CloudShell, config file, or Instance Principals authentication
- **Granular Results** - Shows availability down to the Fault Domain level
- **Flex Shape Support** - Specify custom OCPU and memory configurations
- **GPU Discovery** - Find available GPU instances (A100, H100, A10, V100, L40S) across OCI
- **Rich Output** - Color-coded terminal output with formatted tables

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Check shape availability in your home region
python ocareport.py -shape VM.Standard.E5.Flex

# Check GPU availability across all regions
python ocareport.py -shape BM.GPU.H100.8 -region all
```

## Installation

### From Source

```bash
git clone https://github.com/enricopesce/ocareport.git
cd ocareport
pip install -r requirements.txt
```

### Using pip (editable mode)

```bash
git clone https://github.com/enricopesce/ocareport.git
cd ocareport
pip install -e .
```

## Output Status Meanings

| Status | Description |
|--------|-------------|
| **AVAILABLE** | The capacity for the specified shape is currently available |
| **HARDWARE_NOT_SUPPORTED** | The necessary hardware has not yet been deployed in this region |
| **OUT_OF_HOST_CAPACITY** | Additional hardware is currently being deployed in this region |

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

## Common GPU Shapes

| Shape | GPU | Count | Use Case |
|-------|-----|-------|----------|
| `VM.GPU.A10.1` | NVIDIA A10 | 1 | AI inference, graphics |
| `VM.GPU.A10.2` | NVIDIA A10 | 2 | AI inference, graphics |
| `VM.GPU3.1` | NVIDIA V100 | 1 | Deep learning, HPC |
| `VM.GPU3.2` | NVIDIA V100 | 2 | Deep learning, HPC |
| `VM.GPU3.4` | NVIDIA V100 | 4 | Deep learning, HPC |
| `BM.GPU4.8` | NVIDIA A100 40GB | 8 | Large AI models, HPC |
| `BM.GPU.A100-v2.8` | NVIDIA A100 80GB | 8 | LLM training, large models |
| `BM.GPU.H100.8` | NVIDIA H100 | 8 | Frontier AI, LLM training |
| `BM.GPU.L40S.4` | NVIDIA L40S | 4 | AI inference, rendering |

## Running Tests

```bash
pip install -r requirements.txt
pytest test_ocareport.py -v
```

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
├── pyproject.toml        # Package configuration
├── LICENSE               # MIT License
├── README.md             # This file
├── CHANGELOG.md          # Version history
└── CONTRIBUTING.md       # Contribution guidelines
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Inspired by [OCI_ComputeCapacityReport](https://github.com/Olygo/OCI_ComputeCapacityReport) by Florian Bonneville.

## Contact

Enrico Pesce - [@LinkedIn](https://www.linkedin.com/in/enricopesce/) - [@Blog](https://www.enricopesce.it/)

Project Link: [https://github.com/enricopesce/ocareport](https://github.com/enricopesce/ocareport)

---

**Keywords:** OCI, Oracle Cloud Infrastructure, compute capacity, GPU availability, NVIDIA A100, NVIDIA H100, cloud computing, capacity planning, DevOps, CLI tool
