import oci
import os.path
import os
import argparse
from rich.console import Console
from rich.table import Table
from rich import box
from rich.style import Style
from rich.progress import Progress


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', default='', dest='region',
                        help='Define regions to analyze, default is all regions')
    parser.add_argument('-s', default='', dest='shape', required=True,
                        help='Specify shape name')
    parser.add_argument('-O', default='1', dest='ocpu', required=False,
                        help='Specify ocpu number for flex instances')
    parser.add_argument('-M', default='1', dest='memory', required=False,
                        help='Specify memory quantity in GB for flex instances')

    return parser.parse_args()


def create_and_print_report(core_client, compartment_id, availability_domain, fault_domain, shape, is_flex=False, ocpu=1.0, memory=1.0):
    # Create report details based on whether it's a flex shape or not
    report_details = oci.core.models.CreateComputeCapacityReportDetails(
        compartment_id=compartment_id,
        availability_domain=availability_domain,
        shape_availabilities=[
            oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
                instance_shape=shape,
                fault_domain=fault_domain,
                instance_shape_config=oci.core.models.CapacityReportInstanceShapeConfig(
                    ocpus=ocpu,
                    memory_in_gbs=memory) if is_flex else None)])

    # Create and print the report
    try:
        report = core_client.create_compute_capacity_report(
            create_compute_capacity_report_details=report_details)
    except oci.exceptions.ServiceError as e:
        console.print("error:", cmd.shape, e.message)
        console.print("please check shape names:",
                      "https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm")
        raise SystemExit(1)

    for result in report.data.shape_availabilities:
        if result.availability_status == "AVAILABLE":
            table.add_row(region.region_name, oci_ad, oci_fd, cmd.shape,
                          result.availability_status, style='green')
        else:
            danger_style = Style(color="red", blink=True, bold=True)
            table.add_row(region.region_name, oci_ad, oci_fd, cmd.shape,
                          result.availability_status, style=danger_style)


def get_region_subscription_list(identity_client, tenancy_id, region):
    try:
        subscribed_regions = identity_client.list_region_subscriptions(
            tenancy_id).data

        # create dic region_name:region for each region
        region_map = {
            region.region_name: region for region in subscribed_regions}

        if region:
            region = region_map.get(region.lower())
            if region:
                subscribed_region = []
                subscribed_region.append(region)
                return subscribed_region
            else:
                console.print("Region error:", tenancy_id, region,
                              "Region not subscribed or does not exist")
                raise SystemExit(1)

    except oci.exceptions.ServiceError as e:
        console.print("Region error:", tenancy_id, region, e)
        raise SystemExit(1)

    return subscribed_regions


def get_availability_domains(identity_client, compartment_id):
    oci_ads = []
    availability_domains = oci.pagination.list_call_get_all_results(
        identity_client.list_availability_domains,
        compartment_id).data

    for ad in availability_domains:
        oci_ads.append(ad.name)

    return oci_ads


def get_fault_domains(identity_client, compartment_id, availability_domain):
    oci_fds = []
    fault_domains = oci.pagination.list_call_get_all_results(
        identity_client.list_fault_domains,
        compartment_id, availability_domain).data

    for fd in fault_domains:
        oci_fds.append(fd.name)

    return oci_fds


if __name__ == '__main__':
    script_path = os.path.abspath(__file__)
    script_name = (os.path.basename(script_path))[:-3]

    console = Console()

    progress = Progress()

    cmd = parse_arguments()

    table = Table(title="Shape analyzed: " + cmd.shape + " OCPU: " +
                  cmd.ocpu + " MEMORY: " + cmd.memory, box=box.MARKDOWN)

    table.add_column("REGION", justify="left")
    table.add_column("AVAILABILITY DOMAIN", justify="left")
    table.add_column("FAULT DOMAIN",  justify="left")
    table.add_column("SHAPE", justify="left")
    table.add_column("AVAILABILITY", justify="left")

    config = {}
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    identity_client = oci.identity.IdentityClient(config, signer=signer)
    compute_client = oci.core.ComputeClient(config, signer=signer)

    identity_client = oci.identity.IdentityClient(
        config=config,
        signer=signer)

    my_regions = get_region_subscription_list(
        identity_client,
        signer.tenancy_id,
        cmd.region)

    for region in my_regions:

        config['region'] = region.region_name

        identity_client = oci.identity.IdentityClient(
            config=config, signer=signer)
        core_client = oci.core.ComputeClient(config=config, signer=signer)

        oci_ads = get_availability_domains(identity_client, signer.tenancy_id)

        for oci_ad in oci_ads:
            oci_fds = get_fault_domains(
                identity_client, signer.tenancy_id, oci_ad)

            for oci_fd in oci_fds:
                is_flex = "Flex" in cmd.shape
                create_and_print_report(
                    core_client, signer.tenancy_id, oci_ad, oci_fd, cmd.shape, is_flex, float(cmd.ocpu), float(cmd.memory))

    console.print(table)