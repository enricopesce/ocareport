# OCI Compute Capacity Report (ocareport)

[![PyPI](https://img.shields.io/pypi/v/ocareport.svg)](https://pypi.org/project/ocareport/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OCI SDK](https://img.shields.io/badge/OCI%20SDK-2.149.0+-orange.svg)](https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/)
[![Tests](https://github.com/enricopesce/ocareport/actions/workflows/ci.yml/badge.svg)](https://github.com/enricopesce/ocareport/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Find usable Oracle Cloud Infrastructure compute capacity before you deploy.**

`ocareport` queries the OCI Compute Capacity Report API and shows where a compute shape is available by region, availability domain, and fault domain. It is designed for OCI operators, platform teams, automation engineers, and GPU users who need a quick answer before launching instances or applying Terraform.

## Install

```bash
pip install ocareport
```

Then run:

```bash
ocareport -shape VM.Standard.E5.Flex
```

From source:

```bash
git clone https://github.com/enricopesce/ocareport.git
cd ocareport
pip install -e .
```

## What It Answers

- **Where can I launch this GPU shape?**
- **Which Fault Domain should I choose for a deploy?**
- **Can my CI pipeline stop before Terraform fails?**
- **Can I run a capacity check directly from CloudShell?**
- **How many matching instances does OCI report as available?**

## Use Cases

### Find GPU Capacity

Check a high-demand GPU shape in a target region:

```bash
ocareport -region eu-frankfurt-1 -shape BM.GPU.H100.8
```

Check an A10 VM shape with config-file auth:

```bash
ocareport -auth cf -profile DEFAULT -region eu-frankfurt-1 -shape VM.GPU.A10.2
```

The output includes `STATUS` and `AVAILABLE COUNT`, so you can distinguish unsupported hardware from temporary host capacity exhaustion.

### Choose a Fault Domain for Deploy

Use the `FAULT DOMAIN` rows with `STATUS = AVAILABLE`:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -ocpus 8 -memory 64
```

Example decision:

```text
REGION          AVAILABILITY DOMAIN  FAULT DOMAIN    STATUS     AVAILABLE COUNT
eu-frankfurt-1  AD-1                 FAULT-DOMAIN-1  AVAILABLE  2
eu-frankfurt-1  AD-1                 FAULT-DOMAIN-2  OUT_OF...  0
eu-frankfurt-1  AD-1                 FAULT-DOMAIN-3  AVAILABLE  1
```

Pick `FAULT-DOMAIN-1` or `FAULT-DOMAIN-3` for that deployment.

### Check Before Terraform

Run `ocareport` before `terraform apply` and use its exit code:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -ocpus 8 -memory 64 -output json > capacity.json
terraform apply
```

Exit codes:

| Exit Code | Meaning |
|-----------|---------|
| `0` | At least one Fault Domain has `AVAILABLE` capacity |
| `1` | Technical/API/input error, or an AD-level error with no available capacity found |
| `2` | Query completed but no Fault Domain has available capacity |

### Use in CloudShell

CloudShell auth is auto-detected when the OCI environment variables are present:

```bash
ocareport -shape VM.Standard.E5.Flex
```

Or force CloudShell delegation token auth:

```bash
ocareport -auth cs -region eu-frankfurt-1 -shape BM.GPU.H100.8
```

### Export JSON or CSV

JSON for scripts:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -output json
```

CSV for reports:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -output csv
```

## GitHub Actions Example

Use `ocareport` as a pre-flight capacity check before infrastructure deployment:

```yaml
name: OCI capacity pre-check

on:
  workflow_dispatch:

jobs:
  capacity-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install ocareport

      - name: Check OCI capacity
        run: |
          mkdir -p ~/.oci
          cat > ~/.oci/config <<'EOF'
          [DEFAULT]
          user=${{ secrets.OCI_USER_OCID }}
          fingerprint=${{ secrets.OCI_FINGERPRINT }}
          tenancy=${{ secrets.OCI_TENANCY_OCID }}
          region=eu-frankfurt-1
          key_file=~/.oci/oci_api_key.pem
          EOF
          printf '%s' "${{ secrets.OCI_PRIVATE_KEY }}" > ~/.oci/oci_api_key.pem
          chmod 600 ~/.oci/oci_api_key.pem
          ocareport -auth cf -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -ocpus 8 -memory 64 -output json
```

## Release Workflow

This repository includes a release workflow that runs tests, builds the package, creates a GitHub Release, and publishes to PyPI.

Prepare a release:

```bash
python -m pip install build twine
pytest -q
python -m build
python -m twine check dist/*
```

Create and push a version tag:

```bash
git tag v1.2.0
git push origin v1.2.0
```

The `Release` GitHub Actions workflow will:

1. Run tests on Python 3.8 through 3.12
2. Build source and wheel distributions
3. Validate package metadata with `twine check`
4. Create a GitHub Release with the package artifacts
5. Publish to PyPI

PyPI publishing uses Trusted Publishing. Configure the PyPI project with:

| Field | Value |
|-------|-------|
| Publisher | GitHub |
| Owner | `enricopesce` |
| Repository | `ocareport` |
| Workflow | `release.yml` |
| Environment | `pypi` |

## Authentication

When no authentication method is specified, `ocareport` tries:

1. **CloudShell** - Delegation token, when running in OCI CloudShell
2. **Config File** - Local `~/.oci/config`
3. **Instance Principals** - OCI compute instance identity

You can force a method:

| Method | Flag | Description |
|--------|------|-------------|
| Auto-detect | none | Tries all methods automatically |
| CloudShell | `-auth cs` | Uses OCI CloudShell delegation token |
| Config File | `-auth cf` | Uses local OCI config file |
| Instance Principals | `-auth ip` | Uses OCI compute instance identity |

## CLI Reference

| Argument | Parameter | Description |
|----------|-----------|-------------|
| `-shape` | shape_name | Required. Compute shape name to check |
| `-region` | region_name | Region to analyze. Defaults to home region |
| `-ocpus` | number | OCPU count for flex shapes. Default: `1` |
| `-memory` | number | Memory in GB for flex shapes. Default: `1` |
| `-output` | `table`, `json`, `csv` | Output format. Default: `table` |
| `-auth` | `cs`, `cf`, `ip` | Force a specific authentication method |
| `-config_file` | path | Path to OCI config file. Default: `~/.oci/config` |
| `-profile` | name | Config file profile section. Default: `DEFAULT` |

## Output Status

| Status | Meaning |
|--------|---------|
| `AVAILABLE` | OCI reports capacity for the requested shape/configuration |
| `HARDWARE_NOT_SUPPORTED` | Required hardware is not deployed in that location |
| `OUT_OF_HOST_CAPACITY` | Hardware exists, but OCI reports no current host capacity |
| `ERROR` | An API error occurred for that availability domain; other ADs continue |

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

## Instance Principals Setup

If running from an OCI compute instance, configure Instance Principals authentication.

Dynamic group example:

```text
ANY {instance.id = 'ocid1.instance.oc1.xxx.your_instance_ocid'}
```

Policy example:

```text
allow dynamic-group 'YourDomain'/'OCI_Scripting' to read all-resources in tenancy
```

## Development

```bash
pip install -e ".[dev]"
pytest -q
```

Project structure:

```text
ocareport/
├── ocareport.py
├── modules/
│   ├── __init__.py
│   ├── identity.py
│   └── utils.py
├── test_ocareport.py
├── requirements.txt
├── pyproject.toml
├── LICENSE
├── README.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Credits

Inspired by [OCI_ComputeCapacityReport](https://github.com/Olygo/OCI_ComputeCapacityReport) by Florian Bonneville.

## Contact

Enrico Pesce - [LinkedIn](https://www.linkedin.com/in/enricopesce/) - [Blog](https://www.enricopesce.it/)

Project Link: [https://github.com/enricopesce/ocareport](https://github.com/enricopesce/ocareport)

**Keywords:** OCI, Oracle Cloud Infrastructure, compute capacity, GPU availability, NVIDIA A100, NVIDIA H100, cloud computing, capacity planning, DevOps, Terraform, CloudShell, CLI tool
