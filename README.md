
# Oracle capacity report (ocareport)

An easy tool to verify the availability of compute resources over OCI regions.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contact](#contact)

## Overview

This project is a modification of GitHub project [OCI_ComputeCapacityReport](https://github.com/Olygo/OCI_ComputeCapacityReport) displays a report of the compute host capacity on the OCI provider. 

Is it useful to plan the implementation of the resources, identify if the specific shape is available, and if the resources needed are available.

## Features

- Automatic authentication based on local oci auth configured
- Search by single region or all subscribed regions
- Search by OCPU and MEMORY for Flex shapes

## Installation

The project require only a recent Python and OCI CLI [configured](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm) 

```console
pip install -r requirements
```
## Usage

Verify availability of BM.Standard.E4.128 shapes on all subscribed regions

```console
python ocareport.py -s BM.Standard.E4.128
```

Verify availability of VM.Standard.E5.Flex shapes on Milan region for 24 OCPUS and 512 GB MEMORY

```console
python ocareport.py -s VM.Standard.E5.Flex -r eu-milan-1 -O 24 -M 512
```

## Contact

Enrico Pesce - [@Linkedin](https://www.linkedin.com/in/enricopesce/) - [@Blog](https://www.enricopesce.it/)

Project Link: [https://github.com/enricopesce/ocareport](https://github.com/enricopesce/ocareport)
