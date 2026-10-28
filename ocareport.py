# coding: utf-8
"""
OCI Compute Capacity Report Tool

Check compute shape availability across OCI regions, availability domains,
and fault domains using the Compute Capacity Report API.
"""

import argparse
import csv
import json
import math
import shlex
import sys
from collections import Counter
from contextlib import nullcontext, redirect_stdout

import oci
from rich import box
from rich.console import Console
from rich.table import Table

from modules.utils import green, yellow, print_info, clear
from modules.identity import (
    init_authentication,
    get_region_subscription_list,
    get_availability_domains,
    get_fault_domains
)

VERSION = '1.2.0'


def positive_float(value):
    """Parse a positive float argument."""
    try:
        parsed_value = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid number") from exc

    if not math.isfinite(parsed_value):
        raise argparse.ArgumentTypeError("must be a finite number")
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")

    return parsed_value


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Check OCI compute shape availability in a region'
    )

    # Authentication options
    parser.add_argument('-auth', default='', dest='auth_method',
                        choices=['cs', 'cf', 'ip', ''],
                        help="Authentication method: 'cs' (CloudShell), 'cf' (config file), 'ip' (instance principals)")
    parser.add_argument('-config_file', default='~/.oci/config', dest='config_file_path',
                        help='Path to OCI config file (default: ~/.oci/config)')
    parser.add_argument('-profile', default='DEFAULT', dest='config_profile',
                        help='Config file profile section (default: DEFAULT)')

    # Query options
    parser.add_argument(
        '-region', action='append', dest='regions',
        help='Region(s) to analyze; repeat this option or use comma-separated names (default: home region)'
    )
    parser.add_argument('-shape', default='', dest='shape', required=True,
                        help='Compute shape name to check (required)')
    parser.add_argument('-ocpus', type=positive_float, default=1.0, dest='ocpu',
                        help='OCPU count for flex shapes (default: 1)')
    parser.add_argument('-memory', type=positive_float, default=1.0, dest='memory',
                        help='Memory in GB for flex shapes (default: 1)')
    parser.add_argument('-output', default='table', dest='output_format',
                        choices=['table', 'json', 'csv', 'simple'],
                        help='Output format: table, json, csv, or simple (default: table)')
    parser.add_argument('-available-only', '-available_only', action='store_true',
                        dest='available_only',
                        help='Only display results where the requested capacity is available')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print the command and request summary before the results')

    args = parser.parse_args()
    # Repeated flags and comma-separated input share one string-based region path.
    args.region = ','.join(args.regions or [])
    del args.regions
    return args


def create_capacity_report(core_client, compartment_id, availability_domain,
                           fault_domain, shape, is_flex=False, ocpu=1.0, memory=1.0):
    """
    Query the Compute Capacity Report API for shape availability.

    Returns: availability_status string ('AVAILABLE', 'HARDWARE_NOT_SUPPORTED', 'OUT_OF_HOST_CAPACITY')
    """
    shape_config = None
    if is_flex:
        shape_config = oci.core.models.CapacityReportInstanceShapeConfig(
            ocpus=ocpu,
            memory_in_gbs=memory
        )

    report_details = oci.core.models.CreateComputeCapacityReportDetails(
        compartment_id=compartment_id,
        availability_domain=availability_domain,
        shape_availabilities=[
            oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
                instance_shape=shape,
                fault_domain=fault_domain,
                instance_shape_config=shape_config
            )
        ]
    )

    report = core_client.create_compute_capacity_report(
        create_compute_capacity_report_details=report_details
    )

    return report.data.shape_availabilities[0].availability_status


def create_capacity_report_availabilities(core_client, compartment_id, availability_domain,
                                          shape, fault_domains=None,
                                          is_flex=False, ocpu=1.0, memory=1.0):
    """
    Query shape availability for fault domains in an availability domain.

    Multiple fault domains are requested in one capacity report call so the
    output keeps FD-level detail without one report call per FD.
    """
    shape_config = None
    if is_flex:
        shape_config = oci.core.models.CapacityReportInstanceShapeConfig(
            ocpus=ocpu,
            memory_in_gbs=memory
        )

    if fault_domains:
        shape_availabilities = [
            oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
                instance_shape=shape,
                fault_domain=fault_domain,
                instance_shape_config=shape_config
            )
            for fault_domain in fault_domains
        ]
    else:
        shape_availabilities = [
            oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
                instance_shape=shape,
                instance_shape_config=shape_config
            )
        ]

    report_details = oci.core.models.CreateComputeCapacityReportDetails(
        compartment_id=compartment_id,
        availability_domain=availability_domain,
        shape_availabilities=shape_availabilities
    )

    report = core_client.create_compute_capacity_report(
        create_compute_capacity_report_details=report_details
    )

    return report.data.shape_availabilities


def create_region_clients(base_config, signer, region_name):
    """Create OCI clients for a region without mutating shared config."""
    region_config = dict(base_config)
    region_config['region'] = region_name

    identity_client = oci.identity.IdentityClient(config=region_config, signer=signer)
    core_client = oci.core.ComputeClient(config=region_config, signer=signer)

    return identity_client, core_client


def analyze_region_capacity(base_config, signer, tenancy_id, region,
                            shape, is_flex=False, ocpu=1.0, memory=1.0):
    """Collect capacity rows for a single region."""
    identity_client, core_client = create_region_clients(
        base_config,
        signer,
        region.region_name
    )

    rows = []
    ads = get_availability_domains(identity_client, tenancy_id)

    for ad in ads:
        try:
            fds = get_fault_domains(identity_client, tenancy_id, ad)
            availabilities = create_capacity_report_availabilities(
                core_client, tenancy_id, ad,
                shape, fds, is_flex, ocpu, memory
            )
        except oci.exceptions.ServiceError as e:
            rows.append({
                'region': region.region_name,
                'availability_domain': ad,
                'fault_domain': '-',
                'shape': shape,
                'status': 'ERROR',
                'available_count': None,
                'message': e.message,
            })
            continue

        for availability in availabilities:
            rows.append({
                'region': region.region_name,
                'availability_domain': ad,
                'fault_domain': availability.fault_domain or '-',
                'shape': availability.instance_shape or shape,
                'status': availability.availability_status,
                'available_count': getattr(availability, 'available_count', None),
                'message': '',
            })

    return rows


def get_exit_code(rows):
    """Return automation-friendly exit code for capacity results."""
    if any(row['status'] == 'AVAILABLE' for row in rows):
        return 0
    if any(row['status'] == 'ERROR' for row in rows):
        return 1
    return 2


def render_table(console, rows, shape, ocpu, memory, is_flex=False):
    """Render capacity results as a rich table."""
    title = f"Shape: {shape}"
    if is_flex:
        title += f" | OCPU: {ocpu} | Memory: {memory} GB"

    table = Table(
        title=title,
        box=box.MARKDOWN
    )
    table.add_column("REGION", justify="left")
    table.add_column("AVAILABILITY DOMAIN", justify="left")
    table.add_column("FAULT DOMAIN", justify="left")
    table.add_column("SHAPE", justify="left")
    table.add_column("STATUS", justify="left")
    table.add_column("AVAILABLE COUNT", justify="right")
    table.add_column("MESSAGE", justify="left")

    for row in rows:
        status = row['status']
        if status == 'AVAILABLE':
            style = 'green'
        elif status == 'ERROR':
            style = 'yellow'
        else:
            style = 'red'

        available_count = row['available_count']
        table.add_row(
            row['region'],
            row['availability_domain'],
            row['fault_domain'],
            row['shape'],
            status,
            '-' if available_count is None else str(available_count),
            row['message'],
            style=style
        )

    console.print(table)


def render_json(rows):
    """Render capacity results as JSON."""
    print(json.dumps(rows, indent=2))


def render_csv(rows):
    """Render capacity results as CSV."""
    fieldnames = [
        'region',
        'availability_domain',
        'fault_domain',
        'shape',
        'status',
        'available_count',
        'message',
    ]
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


def render_ascii_chart(rows):
    """Render a simple ASCII bar chart of status distribution for simple text terminals."""
    status_counts = Counter(row['status'] for row in rows)

    max_count = max(status_counts.values()) if status_counts else 0
    bar_width = 40

    print("Availability Status Distribution:")
    print("-" * 50)
    for status in ['AVAILABLE', 'HARDWARE_NOT_SUPPORTED', 'OUT_OF_HOST_CAPACITY', 'ERROR']:
        count = status_counts.get(status, 0)
        bar = '█' * int(count * bar_width / max_count) if max_count > 0 else ''
        print(f"{status:<22} {count:>3} {bar}")
    print("-" * 50)


def main():
    """Main entry point."""
    console = Console()
    args = parse_arguments()
    machine_output = args.output_format in ('json', 'csv')
    is_flex = 'Flex' in args.shape or 'flex' in args.shape

    output_context = redirect_stdout(sys.stderr) if machine_output else nullcontext()
    with output_context:
        if args.verbose:
            if not machine_output:
                clear()
            print(green(f"\n{'*'*94}"))
            print_info(green, 'Command', shlex.join(['python', *sys.argv]))
            print_info(green, 'Version', VERSION)

        # Initialize authentication
        config, signer, tenancy, auth_name, details, tenancy_id = init_authentication(
            args.auth_method,
            args.config_file_path,
            args.config_profile
        )

        # Clear any auth progress messages
        print("\r" + " " * 60 + "\r", end='', flush=True)

        if args.verbose:
            print_info(green, 'Login', 'success')
            print_info(green, 'Auth method', auth_name)
            if auth_name == 'config_file':
                print_info(green, 'Profile', details)
            print_info(green, 'Tenancy', tenancy.name)
            print_info(green, 'Home region', tenancy.home_region_key)

        # Initialize identity client
        identity_client = oci.identity.IdentityClient(config=config, signer=signer)

        # Get region to analyze
        regions = get_region_subscription_list(
            identity_client,
            tenancy_id,
            args.region
        )

        if args.verbose:
            print_info(green, 'Shape', args.shape)
            if is_flex:
                print_info(green, 'OCPUs', f'{args.ocpu} cores')
                print_info(green, 'Memory', f'{args.memory} GB')
            if args.available_only:
                print_info(green, 'Filter', 'available only')

            print(green(f"{'*'*94}\n"))

    rows = []

    try:
        for region in regions:
            region_rows = analyze_region_capacity(
                config,
                signer,
                tenancy_id,
                region,
                args.shape,
                is_flex,
                args.ocpu,
                args.memory
            )
            rows.extend(region_rows)

    except oci.exceptions.ServiceError as e:
        print(f"Error: {args.shape} - {e.message}", file=sys.stderr)
        print("Check shape names: https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm", file=sys.stderr)
        raise SystemExit(1)

    # Filter presentation only; exit codes continue to use every API result.
    display_rows = (
        [row for row in rows if row['status'] == 'AVAILABLE']
        if args.available_only else rows
    )

    if args.output_format == 'json':
        render_json(display_rows)
    elif args.output_format == 'csv':
        render_csv(display_rows)
    elif args.output_format == 'simple':
        if display_rows:
            render_ascii_chart(display_rows)
        else:
            print("No results to display.")
    else:
        render_table(console, display_rows, args.shape, args.ocpu, args.memory, is_flex)

    raise SystemExit(get_exit_code(rows))


if __name__ == '__main__':
    main()
