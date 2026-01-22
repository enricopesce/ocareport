# coding: utf-8
"""
OCI Compute Capacity Report Tool

Check compute shape availability across OCI regions, availability domains,
and fault domains using the Compute Capacity Report API.
"""

import argparse
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

VERSION = '1.1.0'


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Check OCI compute shape availability across regions'
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
    parser.add_argument('-region', default='', dest='region',
                        help="Region to analyze: specific region name, 'all' for all regions, or empty for home region")
    parser.add_argument('-shape', default='', dest='shape', required=True,
                        help='Compute shape name to check (required)')
    parser.add_argument('-ocpus', type=float, default=1, dest='ocpu',
                        help='OCPU count for flex shapes (default: 1)')
    parser.add_argument('-memory', type=float, default=1, dest='memory',
                        help='Memory in GB for flex shapes (default: 1)')

    return parser.parse_args()


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


def main():
    """Main entry point."""
    clear()
    console = Console()
    args = parse_arguments()

    # Print banner
    print(green(f"\n{'*'*94}"))
    print_info(green, 'Script', 'version', VERSION)

    # Initialize authentication
    config, signer, tenancy, auth_name, details, tenancy_id = init_authentication(
        args.auth_method,
        args.config_file_path,
        args.config_profile
    )

    # Clear any auth progress messages
    print("\r" + " " * 60 + "\r", end='', flush=True)

    print_info(green, 'Login', 'success', auth_name)
    print_info(green, 'Login', 'profile', details)
    print_info(green, 'Tenancy', tenancy.name, f'home region: {tenancy.home_region_key}')

    # Initialize identity client
    identity_client = oci.identity.IdentityClient(config=config, signer=signer)

    # Get regions to analyze
    regions = get_region_subscription_list(
        identity_client,
        tenancy_id,
        args.region
    )

    # Print shape info
    print_info(green, 'Shape', 'analyzed', args.shape)
    if 'Flex' in args.shape or 'flex' in args.shape:
        print_info(green, 'OCPUs', 'amount', f'{args.ocpu} cores')
        print_info(green, 'Memory', 'amount', f'{args.memory} GB')

    print(green(f"{'*'*94}\n"))

    # Create results table
    table = Table(
        title=f"Shape: {args.shape} | OCPU: {args.ocpu} | Memory: {args.memory} GB",
        box=box.MARKDOWN
    )
    table.add_column("REGION", justify="left")
    table.add_column("AVAILABILITY DOMAIN", justify="left")
    table.add_column("FAULT DOMAIN", justify="left")
    table.add_column("SHAPE", justify="left")
    table.add_column("STATUS", justify="left")

    is_flex = 'Flex' in args.shape or 'flex' in args.shape

    # Query each region/AD/FD combination
    for region in regions:
        config['region'] = region.region_name
        identity_client = oci.identity.IdentityClient(config=config, signer=signer)
        core_client = oci.core.ComputeClient(config=config, signer=signer)

        ads = get_availability_domains(identity_client, tenancy_id)

        for ad in ads:
            fds = get_fault_domains(identity_client, tenancy_id, ad)

            for fd in fds:
                try:
                    status = create_capacity_report(
                        core_client, tenancy_id, ad, fd,
                        args.shape, is_flex, args.ocpu, args.memory
                    )

                    style = 'green' if status == 'AVAILABLE' else 'red'
                    table.add_row(region.region_name, ad, fd, args.shape, status, style=style)

                except oci.exceptions.ServiceError as e:
                    console.print(f"[red]Error:[/red] {args.shape} - {e.message}")
                    console.print("Check shape names: https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm")
                    raise SystemExit(1)

    console.print(table)


if __name__ == '__main__':
    main()
