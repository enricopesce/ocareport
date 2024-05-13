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
    parser.add_argument('-cs', action='store_true', default=False, dest='is_delegation_token',
                        help='Use CloudShell Delegation Token for authentication')
    parser.add_argument('-cf', action='store_true', default=False, dest='is_config_file',
                        help='Use local OCI config file for authentication')
    parser.add_argument('-cfp', default='~/.oci/config', dest='config_file_path',
                        help='Path to your OCI config file, default: ~/.oci/config')
    parser.add_argument('-cp', default='DEFAULT', dest='config_profile',
                        help='Config file section to use, default: DEFAULT')    
    parser.add_argument('-r', default='', dest='region',
                        help='Define regions to analyze, default is all regions')
    parser.add_argument('-s', default='', dest='shape', required=True,
                        help='Specify shape name')
    parser.add_argument('-O', default='1', dest='ocpu', required=False,
                        help='Specify ocpu number for flex instances')
    parser.add_argument('-M', default='1', dest='memory', required=False,
                        help='Specify memory quantity in GB for flex instances')

    return parser.parse_args()


def get_tenancy(tenancy_id, config, signer):

    identity = oci.identity.IdentityClient(config=config, signer=signer)
    try:
        tenancy = identity.get_tenancy(tenancy_id)
        home_region_key = f'home region: {tenancy.data.home_region_key}'
    except oci.exceptions.ServiceError as e:
        console.print("Tenancy error:", tenancy_id, e.code, e.message)
        raise SystemExit(1)

    return tenancy.data.name, home_region_key


def create_signer(config_file_path, config_profile, is_delegation_token, is_config_file):

    custom_retry_strategy = oci.retry.RetryStrategyBuilder(
                                max_attempts_check=True,
                                max_attempts=3,
                                total_elapsed_time_check=True,
                                total_elapsed_time_seconds=20,
                                retry_max_wait_between_calls_seconds=5,
                                retry_base_sleep_time_seconds=2,
                                ).get_retry_strategy()    

    # --------------------------------
    # Config File authentication
    # --------------------------------
    if is_config_file:
        try:
            config = oci.config.from_file(file_location=config_file_path, profile_name=config_profile)
            oci.config.validate_config(config) # raise an error if error in config

            signer = oci.signer.Signer(
                tenancy=config['tenancy'],
                user=config['user'],
                fingerprint=config['fingerprint'],
                private_key_file_location=config.get('key_file'),
                pass_phrase=oci.config.get_config_value_or_default(config, 'pass_phrase'),
                private_key_content=config.get('key_content')
            )
            # try getting namespace to validate config
            oci.object_storage.ObjectStorageClient(config=config, signer=signer).get_namespace()

            console.print('Login', 'success', 'config_file')
            console.print('Login', 'profile', config_profile)

            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)
            console.print('Tenancy', oci_tname, oci_tregion)

            return config, signer, oci_tname

        except oci.exceptions.ServiceError as e:
            console.print("Something went wrong with file content:", config_file_path, config_profile, e.code, e.message)
            raise SystemExit(1)

        except Exception as e:
            console.print(e)
            raise SystemExit(1)
    
    # --------------------------------
    # Delegation Token authentication
    # --------------------------------
    elif is_delegation_token:

        try:
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')
            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config['delegation_token_file']
            oci.config.validate_config(config) # raise an error if error in config

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)

            # try getting namespace to validate config
            oci.object_storage.ObjectStorageClient(config=config, signer=signer).get_namespace()

            console.print('Login', 'success', 'delegation_token')
            console.print('Login', 'token', delegation_token_location)

            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)
            console.print('Tenancy', oci_tname, oci_tregion)

            return config, signer, oci_tname

        except oci.exceptions.ServiceError as e:
            console.print("CloudShell authentication error:", e)
            raise SystemExit(1)
        
        except Exception as e:
            console.print("CloudShell authentication error:", e)
            raise SystemExit(1)
        
    # -----------------------------------
    # Instance Principals authentication
    # -----------------------------------
    else:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner(retry_strategy=custom_retry_strategy)
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
          
            oci_tname, oci_tregion = get_tenancy(config['tenancy'], config, signer)

            # try getting namespace to validate config
            oci.object_storage.ObjectStorageClient(config=config, signer=signer).get_namespace()

            console.print('Login', 'success', 'instance_principals')
            console.print('Tenancy', oci_tname, oci_tregion)

            return config, signer, oci_tname

        except oci.exceptions.ServiceError as e:
            console.print("Instance_Principals authentication error:", e)
            raise SystemExit(1)

        except Exception as e:
            console.print("Instance Principals authentication error:", e)
            raise SystemExit(1)
        

def create_and_print_report(core_client, compartment_id, availability_domain, fault_domain, shape, is_flex=False, ocpu=1.0, memory=1.0):
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
            table.add_row(region.region_name, oci_ad, oci_fd, cmd.shape,
                          result.availability_status,  style='red')


def get_region_subscription_list(identity_client, tenancy_id, region):
    try:
        subscribed_regions = identity_client.list_region_subscriptions(
            tenancy_id).data

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

    config, signer, oci_tname=create_signer(cmd.config_file_path, 
                                            cmd.config_profile, 
                                            cmd.is_delegation_token, 
                                            cmd.is_config_file)
 
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
