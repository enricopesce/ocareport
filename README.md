# OCI Compute Capacity Report (ocareport)

[![PyPI](https://img.shields.io/pypi/v/ocareport.svg)](https://pypi.org/project/ocareport/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OCI SDK](https://img.shields.io/badge/OCI%20SDK-2.149.0+-orange.svg)](https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Find usable Oracle Cloud Infrastructure compute capacity before you deploy.**

`ocareport` queries the OCI Compute Capacity Report API and shows where a compute shape is available by region, availability domain, and fault domain. It is designed for OCI operators, platform teams, and automation engineers who need a quick answer before launching instances.

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

## OCI APIs Used

`ocareport` queries several OCI APIs via the OCI Python SDK (v2.189.0) to produce the capacity report. Each API is called through the SDK's `oci` module and requires a valid OCI user with read permissions on the tenancy.

### 1. OCI Compute Capacity Report API
- **Endpoint**: `POST /opc/v2/compute/capacity-report`
- **SDK call**: `oci.core.ComputeClient.create_compute_capacity_report(...)`
- **Purpose**: Check compute shape availability across regions, availability domains, and fault domains
- **Key operations**:
  - `CreateCapacityReportDetails` — builds the request body for the capacity report
  - `CreateCapacityReportShapeAvailabilityDetails` — defines the shape config (OCPUs, memory) and fault domain for the report
  - `CreateCapacityReport` — executes the report query
- **Response**: `shape_availabilities` array, each with `availability_status`
- **Statuses returned**: `AVAILABLE`, `HARDWARE_NOT_SUPPORTED`, `OUT_OF_HOST_CAPACITY`, `ERROR`
- **Auth**: Requires a valid OCI user with read permissions on the tenancy

### 2. OCI Identity API
- **Endpoint**: `GET /opc/v2/identity/tenancy` (via `IdentityClient.get_tenancy`)
- **Purpose**: Fetch the tenancy's home region and validate the signer's tenancy
- **Used by**: `authenticate_cloud_shell` and `authenticate_instance_principals` to validate the signer's tenancy

### 3. OCI Config API
- **Endpoint**: `GET /config` (via `oci.config.from_file`)
- **Purpose**: Read the OCI config file (`~/.oci/config`) containing user, fingerprint, tenancy, region, and key file
- **Used by**: `authenticate_config_file` to load credentials

### 4. OCI Tenancy API
- **Endpoint**: `GET /tenancy` (via `IdentityClient.get_tenancy`)
- **Purpose**: Retrieve the tenancy's home region and other metadata
- **Used by**: `authenticate_cloud_shell` and `authenticate_instance_principals` to validate the signer's tenancy

### 5. OCI Region API
- **Endpoint**: `GET /regions` (via `IdentityClient.list_region_subscriptions`)
- **Purpose**: List the regions where the tenancy is subscribed
- **Used by**: `get_region_subscription_list` to determine which regions to query

### 6. OCI Availability Domain API
- **Endpoint**: `GET /availability-domains` (via `IdentityClient.list_availability_domains`)
- **Purpose**: List the availability domains within a region
- **Used by**: `get_availability_domains` to enumerate ADs for the region

### 7. OCI Fault Domain API
- **Endpoint**: `GET /fault-domains` (via `IdentityClient.list_fault_domains`)
- **Purpose**: List the fault domains within an availability domain
- **Used by**: `get_fault_domains` to enumerate FD options for the shape

### Authentication
All API calls are authenticated via the OCI SDK's signer mechanism. The tool supports three auth methods:
1. **CloudShell** — delegation token from the OCI CloudShell environment
2. **Config File** — local `~/.oci/config` with user credentials
3. **Instance Principals** — OCI compute instance identity (requires running on an OCI compute instance)

## What It Answers

- **Where can I launch this compute shape?**
- **Which Fault Domain should I choose for a deploy?**
- **Can I run a capacity check directly from CloudShell?**
- **How many matching instances does OCI report as available?****

## Use Cases

### Check Compute CPU Capacity

Check a flexible AMD E5 VM with 8 OCPUs and 64 GB memory:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -ocpus 8 -memory 64
```

Check an Intel X9 flexible VM:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard3.Flex -ocpus 4 -memory 32
```

Check an Ampere A1 ARM flexible VM:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard.A1.Flex -ocpus 4 -memory 24
```

Check a dense I/O bare metal shape:

```bash
ocareport -region eu-frankfurt-1 -shape BM.DenseIO.E4.128
```

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

### Find Available Capacity Across Regions

Check a shape in multiple subscribed regions and show only locations where OCI reports capacity:

```bash
ocareport -shape VM.GPU.A10.1 \
  -region eu-frankfurt-1,us-ashburn-1 \
  -available-only
```

You can also repeat `-region` instead of using a comma-separated list:

```bash
ocareport -shape VM.GPU.A10.1 \
  -region eu-frankfurt-1 -region us-ashburn-1 \
  -available-only
```

If you need to check which regions your tenancy is subscribed to, run:

```bash
oci iam region-subscription list --all
```

The report has one row per availability domain and fault domain. When OCI returns `available_count`, it is the number of new instances for that location. OCI can omit this optional field; in that case the table shows `N/A`, while JSON/CSV contain a null or empty value. `AVAILABLE` confirms capacity is available but does not reveal its exact count. Add counts by region only when OCI returned numbers for all relevant rows. Export CSV for aggregation:

```bash
ocareport -shape VM.GPU.A10.1 \
  -region eu-frankfurt-1,us-ashburn-1 \
  -available-only -output csv
```

Replace the example regions with regions subscribed to your tenancy. The tool checks only the home region when `-region` is omitted.


### Use in CloudShell

CloudShell auth is auto-detected when the OCI environment variables are present. Install or update `ocareport` in CloudShell:

```bash
python3 -m pip install --user --upgrade ocareport
```

Then run a capacity check:

```bash
ocareport -shape VM.Standard.E5.Flex
```

Or force CloudShell delegation token auth:

```bash
ocareport -auth cs -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -ocpus 4 -memory 32
```

CloudShell already has an OCI delegation token, so you do not need a local `~/.oci/config` file or API key inside CloudShell. If you omit `-region`, `ocareport` uses your tenancy home region when it can discover it. Pass `-region` when you want to check a specific OCI region.

### Export JSON or CSV

JSON for scripts:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -output json
```

CSV for reports:

```bash
ocareport -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -output csv
```

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

### Local Config File Setup

For a laptop, workstation, or jump host, configure OCI SDK authentication in `~/.oci/config`.

Create the config directory and generate an API signing key:

```bash
mkdir -p ~/.oci
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
chmod 600 ~/.oci/oci_api_key.pem
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
```

Upload the public key in the OCI Console:

1. Open **Profile** > **User settings** > **API keys**
2. Add the contents of `~/.oci/oci_api_key_public.pem`
3. Copy the generated fingerprint

Create `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..example
fingerprint=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
tenancy=ocid1.tenancy.oc1..example
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key.pem
```

Then run:

```bash
ocareport -auth cf -shape VM.Standard.E5.Flex -ocpus 4 -memory 32
```

Use a named profile when you manage multiple tenancies or users:

```ini
[PROD]
user=ocid1.user.oc1..example
fingerprint=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
tenancy=ocid1.tenancy.oc1..example
region=eu-frankfurt-1
key_file=~/.oci/prod_api_key.pem
```

```bash
ocareport -auth cf -profile PROD -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -ocpus 8 -memory 64
```

If your config file is in a different location:

```bash
ocareport -auth cf -config_file /path/to/oci-config -profile PROD -shape VM.Standard.A1.Flex -ocpus 4 -memory 24
```

### CloudShell Setup

In OCI CloudShell, install the package for your CloudShell user and run with CloudShell auth:

```bash
python3 -m pip install --user --upgrade ocareport
ocareport -auth cs -region eu-frankfurt-1 -shape VM.Standard.E5.Flex -ocpus 4 -memory 32
```

CloudShell sessions are ephemeral enough that using `--user --upgrade` is usually the simplest install path. Re-run the install command when you need a newer `ocareport` version.

### Required OCI Permissions

The authenticated principal must be allowed to inspect compute capacity reports and read the tenancy region metadata used by the tool. A broad read policy is simple for testing:

```text
allow group 'YourDomain'/'YourGroup' to read all-resources in tenancy
```

For tighter production policies, grant only the minimum read/inspect permissions your tenancy requires for Compute capacity report and Identity region lookups.

## CLI Reference

| Argument | Parameter | Description |
|----------|-----------|-------------|
| `-shape` | shape_name | Required. Compute shape name to check |
| `-region` | region_name | Region to analyze; repeat the flag or use comma-separated names. Defaults to home region |
| `-ocpus` | number | OCPU count for flex shapes. Default: `1` |
| `-memory` | number | Memory in GB for flex shapes. Default: `1` |
| `-output` | `table`, `json`, `csv`, `simple` | Output format. Default: `table` |
| `-available-only` | — | Display only rows with `AVAILABLE` status |
| `-v`, `--verbose` | — | Print the command and request summary before results |
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

## Common Compute CPU Shapes

| Shape | Processor Family | Type | Use Case |
|-------|------------------|------|----------|
| `VM.Standard.E5.Flex` | AMD EPYC | Flexible VM | General purpose apps, services, databases |
| `VM.Standard.E4.Flex` | AMD EPYC | Flexible VM | General purpose apps, dev/test, batch jobs |
| `VM.Standard3.Flex` | Intel Xeon | Flexible VM | Enterprise workloads, x86 compatibility |
| `VM.Standard.A1.Flex` | Ampere Altra | Flexible VM | ARM-native apps, cost-optimized services |
| `BM.Standard.E5.192` | AMD EPYC | Bare metal | High-core-count compute workloads |
| `BM.DenseIO.E4.128` | AMD EPYC | Bare metal | Local NVMe storage, data platforms |

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

**Keywords:** OCI, Oracle Cloud Infrastructure, compute capacity, CPU capacity, cloud computing, capacity planning, DevOps, CloudShell, CLI tool
