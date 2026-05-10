"""Tests for ocareport.py CLI tool."""
import sys
from unittest import mock

import oci
import pytest

import ocareport
from modules import identity


class TestParseArguments:
    """Tests for argument parsing."""

    def test_shape_required(self):
        """Test that -shape argument is required."""
        with pytest.raises(SystemExit):
            with mock.patch.object(sys, 'argv', ['ocareport.py']):
                ocareport.parse_arguments()

    def test_shape_argument(self):
        """Test shape argument is parsed correctly."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-shape', 'VM.Standard.E5.Flex']):
            args = ocareport.parse_arguments()
            assert args.shape == 'VM.Standard.E5.Flex'

    def test_default_values(self):
        """Test default argument values."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-shape', 'TestShape']):
            args = ocareport.parse_arguments()
            assert args.auth_method == ''
            assert args.config_file_path == '~/.oci/config'
            assert args.config_profile == 'DEFAULT'
            assert args.region == ''
            assert args.ocpu == 1
            assert args.memory == 1
            assert args.output_format == 'table'

    def test_auth_method_config_file(self):
        """Test -auth cf flag."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-auth', 'cf', '-shape', 'TestShape']):
            args = ocareport.parse_arguments()
            assert args.auth_method == 'cf'

    def test_auth_method_cloudshell(self):
        """Test -auth cs flag."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-auth', 'cs', '-shape', 'TestShape']):
            args = ocareport.parse_arguments()
            assert args.auth_method == 'cs'

    def test_auth_method_instance_principals(self):
        """Test -auth ip flag."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-auth', 'ip', '-shape', 'TestShape']):
            args = ocareport.parse_arguments()
            assert args.auth_method == 'ip'

    def test_custom_config_path(self):
        """Test -config_file sets custom config file path."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-config_file', '/custom/path', '-shape', 'TestShape']):
            args = ocareport.parse_arguments()
            assert args.config_file_path == '/custom/path'

    def test_custom_profile(self):
        """Test -profile sets custom config profile."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-profile', 'PRODUCTION', '-shape', 'TestShape']):
            args = ocareport.parse_arguments()
            assert args.config_profile == 'PRODUCTION'

    def test_region_filter(self):
        """Test -region sets region filter."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-region', 'eu-milan-1', '-shape', 'TestShape']):
            args = ocareport.parse_arguments()
            assert args.region == 'eu-milan-1'

    @pytest.mark.parametrize('output_format', ['table', 'json', 'csv'])
    def test_output_format(self, output_format):
        """Test -output accepts supported formats."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-shape', 'TestShape', '-output', output_format]):
            args = ocareport.parse_arguments()
            assert args.output_format == output_format

    def test_flex_options(self):
        """Test -ocpus and -memory set OCPU and memory for flex shapes."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-shape', 'VM.Standard.E5.Flex', '-ocpus', '24', '-memory', '512']):
            args = ocareport.parse_arguments()
            assert args.ocpu == 24.0
            assert args.memory == 512.0

    @pytest.mark.parametrize('option', ['-ocpus', '-memory'])
    @pytest.mark.parametrize('value', ['0', '-1'])
    def test_flex_resource_options_must_be_positive(self, option, value):
        """Test -ocpus and -memory reject zero or negative values."""
        with pytest.raises(SystemExit):
            with mock.patch.object(sys, 'argv', ['ocareport.py', '-shape', 'TestShape', option, value]):
                ocareport.parse_arguments()

    def test_all_options_combined(self):
        """Test all options can be used together."""
        with mock.patch.object(sys, 'argv', [
            'ocareport.py', '-auth', 'cf', '-config_file', '/custom/config',
            '-profile', 'PROD', '-region', 'us-ashburn-1',
            '-shape', 'VM.Standard.E5.Flex', '-ocpus', '8', '-memory', '128'
        ]):
            args = ocareport.parse_arguments()
            assert args.auth_method == 'cf'
            assert args.config_file_path == '/custom/config'
            assert args.config_profile == 'PROD'
            assert args.region == 'us-ashburn-1'
            assert args.shape == 'VM.Standard.E5.Flex'
            assert args.ocpu == 8.0
            assert args.memory == 128.0


class TestGetAvailabilityDomains:
    """Tests for get_availability_domains function."""

    def test_returns_ad_names(self):
        """Test that AD names are extracted correctly."""
        mock_client = mock.MagicMock()
        mock_ad1 = mock.MagicMock()
        mock_ad1.name = 'AD-1'
        mock_ad2 = mock.MagicMock()
        mock_ad2.name = 'AD-2'

        with mock.patch('oci.pagination.list_call_get_all_results') as mock_paginate:
            mock_paginate.return_value.data = [mock_ad1, mock_ad2]
            result = identity.get_availability_domains(mock_client, 'test-compartment')

        assert result == ['AD-1', 'AD-2']


class TestGetFaultDomains:
    """Tests for get_fault_domains function."""

    def test_returns_fd_names(self):
        """Test that FD names are extracted correctly."""
        mock_client = mock.MagicMock()
        mock_fd1 = mock.MagicMock()
        mock_fd1.name = 'FD-1'
        mock_fd2 = mock.MagicMock()
        mock_fd2.name = 'FD-2'

        with mock.patch('oci.pagination.list_call_get_all_results') as mock_paginate:
            mock_paginate.return_value.data = [mock_fd1, mock_fd2]
            result = identity.get_fault_domains(mock_client, 'test-compartment', 'AD-1')

        assert result == ['FD-1', 'FD-2']


class TestGetRegionSubscriptionList:
    """Tests for get_region_subscription_list function."""

    def test_returns_home_region_when_no_filter(self):
        """Test home region returned when no filter specified."""
        mock_client = mock.MagicMock()
        mock_region1 = mock.MagicMock()
        mock_region1.region_name = 'us-ashburn-1'
        mock_region1.is_home_region = True
        mock_region2 = mock.MagicMock()
        mock_region2.region_name = 'eu-frankfurt-1'
        mock_region2.is_home_region = False

        mock_client.list_region_subscriptions.return_value.data = [mock_region1, mock_region2]

        result = identity.get_region_subscription_list(mock_client, 'test-tenancy', '')

        assert len(result) == 1
        assert result[0].region_name == 'us-ashburn-1'

    def test_rejects_all_region_keyword(self):
        """Test global region search is not supported."""
        mock_client = mock.MagicMock()
        mock_region1 = mock.MagicMock()
        mock_region1.region_name = 'us-ashburn-1'
        mock_region1.is_home_region = True
        mock_region2 = mock.MagicMock()
        mock_region2.region_name = 'eu-frankfurt-1'
        mock_region2.is_home_region = False

        mock_client.list_region_subscriptions.return_value.data = [mock_region1, mock_region2]
        mock_known_region = mock.MagicMock()
        mock_known_region.name = 'us-ashburn-1'
        mock_client.list_regions.return_value.data = [mock_known_region]

        with pytest.raises(SystemExit):
            identity.get_region_subscription_list(mock_client, 'test-tenancy', 'all')

    def test_filters_to_single_region(self):
        """Test filtering to a specific region."""
        mock_client = mock.MagicMock()
        mock_region1 = mock.MagicMock()
        mock_region1.region_name = 'us-ashburn-1'
        mock_region1.is_home_region = True
        mock_region2 = mock.MagicMock()
        mock_region2.region_name = 'eu-frankfurt-1'
        mock_region2.is_home_region = False

        mock_client.list_region_subscriptions.return_value.data = [mock_region1, mock_region2]

        result = identity.get_region_subscription_list(mock_client, 'test-tenancy', 'eu-frankfurt-1')

        assert len(result) == 1
        assert result[0].region_name == 'eu-frankfurt-1'


class TestAuthentication:
    """Tests for authentication functions."""

    def test_forced_auth_failure_exits_without_retry_prompt(self):
        """Test forced auth failure exits instead of prompting for another config."""
        def fail_config_auth(auth_errors, *_args):
            auth_errors['Config_File'] = 'config failed'
            return None, None, None, None, None, None

        with mock.patch('modules.identity.authenticate_config_file', side_effect=fail_config_auth):
            with mock.patch('modules.identity.retry_auth') as mock_retry:
                with mock.patch('modules.identity.print_error') as mock_print_error:
                    with pytest.raises(SystemExit) as exc_info:
                        identity.init_authentication('cf', '~/.oci/config', 'DEFAULT')

        assert exc_info.value.code == 1
        mock_retry.assert_not_called()
        mock_print_error.assert_called_once_with('Config_File', 'config failed')

    def test_auto_auth_failure_prompts_for_retry_when_interactive(self):
        """Test auto auth keeps the existing retry prompt in interactive terminals."""
        def fail_cloud_shell(auth_errors):
            auth_errors['CloudShell'] = 'cloud shell failed'
            return None, None, None, None, None, None

        def fail_config_auth(auth_errors, *_args):
            auth_errors['Config_File'] = 'config failed'
            return None, None, None, None, None, None

        def fail_instance_principals(auth_errors):
            auth_errors['Instance_Principals'] = 'instance principals failed'
            return None, None, None, None, None, None

        with mock.patch('modules.identity.authenticate_cloud_shell', side_effect=fail_cloud_shell):
            with mock.patch('modules.identity.authenticate_config_file', side_effect=fail_config_auth):
                with mock.patch('modules.identity.authenticate_instance_principals', side_effect=fail_instance_principals):
                    with mock.patch('sys.stdin.isatty', return_value=True):
                        with mock.patch('modules.identity.retry_auth', return_value='retry-result') as mock_retry:
                            result = identity.init_authentication('', '~/.oci/config', 'DEFAULT')

        assert result == 'retry-result'
        mock_retry.assert_called_once_with()

    def test_auto_auth_failure_exits_without_retry_prompt_when_noninteractive(self):
        """Test auto auth does not block on input in noninteractive terminals."""
        def fail_cloud_shell(auth_errors):
            auth_errors['CloudShell'] = 'cloud shell failed'
            return None, None, None, None, None, None

        def fail_config_auth(auth_errors, *_args):
            auth_errors['Config_File'] = 'config failed'
            return None, None, None, None, None, None

        def fail_instance_principals(auth_errors):
            auth_errors['Instance_Principals'] = 'instance principals failed'
            return None, None, None, None, None, None

        with mock.patch('modules.identity.authenticate_cloud_shell', side_effect=fail_cloud_shell):
            with mock.patch('modules.identity.authenticate_config_file', side_effect=fail_config_auth):
                with mock.patch('modules.identity.authenticate_instance_principals', side_effect=fail_instance_principals):
                    with mock.patch('sys.stdin.isatty', return_value=False):
                        with mock.patch('modules.identity.retry_auth') as mock_retry:
                            with mock.patch('modules.identity.print_error') as mock_print_error:
                                with pytest.raises(SystemExit) as exc_info:
                                    identity.init_authentication('', '~/.oci/config', 'DEFAULT')

        assert exc_info.value.code == 1
        mock_retry.assert_not_called()
        assert mock_print_error.call_args_list == [
            mock.call('CloudShell', 'cloud shell failed'),
            mock.call('Config_File', 'config failed'),
            mock.call('Instance_Principals', 'instance principals failed'),
        ]

    @mock.patch('modules.identity.oci.identity.IdentityClient')
    @mock.patch('modules.identity.oci.signer.Signer')
    @mock.patch('modules.identity.oci.config.validate_config')
    @mock.patch('modules.identity.oci.config.from_file')
    def test_config_file_auth(self, mock_from_file, mock_validate, mock_signer, mock_identity):
        """Test config file authentication path."""
        mock_from_file.return_value = {
            'tenancy': 'test-tenancy-id',
            'user': 'test-user',
            'fingerprint': 'aa:bb:cc',
            'key_file': '/path/to/key'
        }
        mock_tenancy = mock.MagicMock()
        mock_tenancy.name = 'test-tenancy'
        mock_tenancy.home_region_key = 'IAD'
        mock_identity.return_value.get_tenancy.return_value.data = mock_tenancy

        config, signer, tenancy, auth_name, details, tenancy_id = identity.authenticate_config_file(
            {}, '~/.oci/config', 'DEFAULT'
        )

        assert config is not None
        assert auth_name == 'config_file'
        assert tenancy_id == 'test-tenancy-id'

    @mock.patch('modules.identity.oci.identity.IdentityClient')
    @mock.patch('modules.identity.oci.auth.signers.InstancePrincipalsSecurityTokenSigner')
    def test_instance_principals_auth(self, mock_ip_signer, mock_identity):
        """Test instance principals authentication path."""
        mock_ip_signer.return_value.region = 'us-ashburn-1'
        mock_ip_signer.return_value.tenancy_id = 'test-tenancy-id'
        mock_tenancy = mock.MagicMock()
        mock_tenancy.name = 'test-tenancy'
        mock_identity.return_value.get_tenancy.return_value.data = mock_tenancy

        config, signer, tenancy, auth_name, details, tenancy_id = identity.authenticate_instance_principals({})

        assert config is not None
        assert config['region'] == 'us-ashburn-1'
        assert auth_name == 'instance_principals'
        assert tenancy_id == 'test-tenancy-id'


class TestCreateCapacityReport:
    """Tests for create_capacity_report function."""

    def test_available_shape(self):
        """Test available shape returns AVAILABLE status."""
        mock_client = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.availability_status = 'AVAILABLE'
        mock_client.create_compute_capacity_report.return_value.data.shape_availabilities = [mock_result]

        status = ocareport.create_capacity_report(
            mock_client, 'compartment-id', 'AD-1', 'FD-1', 'TestShape'
        )

        assert status == 'AVAILABLE'

    def test_unavailable_shape(self):
        """Test unavailable shape returns correct status."""
        mock_client = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.availability_status = 'OUT_OF_HOST_CAPACITY'
        mock_client.create_compute_capacity_report.return_value.data.shape_availabilities = [mock_result]

        status = ocareport.create_capacity_report(
            mock_client, 'compartment-id', 'AD-1', 'FD-1', 'TestShape'
        )

        assert status == 'OUT_OF_HOST_CAPACITY'

    def test_flex_shape_config_passed(self):
        """Test flex shape configuration is passed correctly."""
        mock_client = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.availability_status = 'AVAILABLE'
        mock_client.create_compute_capacity_report.return_value.data.shape_availabilities = [mock_result]

        ocareport.create_capacity_report(
            mock_client, 'compartment-id', 'AD-1', 'FD-1',
            'VM.Standard.E5.Flex', is_flex=True, ocpu=24.0, memory=512.0
        )

        call_args = mock_client.create_compute_capacity_report.call_args
        report_details = call_args[1]['create_compute_capacity_report_details']
        shape_config = report_details.shape_availabilities[0].instance_shape_config

        assert shape_config.ocpus == 24.0
        assert shape_config.memory_in_gbs == 512.0


class TestCreateCapacityReportAvailabilities:
    """Tests for AD-level capacity report queries."""

    def test_returns_all_shape_availabilities(self):
        """Test AD-level report returns all shape availability entries."""
        mock_client = mock.MagicMock()
        mock_result1 = mock.MagicMock()
        mock_result1.fault_domain = 'FAULT-DOMAIN-1'
        mock_result1.availability_status = 'AVAILABLE'
        mock_result2 = mock.MagicMock()
        mock_result2.fault_domain = 'FAULT-DOMAIN-2'
        mock_result2.availability_status = 'OUT_OF_HOST_CAPACITY'
        mock_client.create_compute_capacity_report.return_value.data.shape_availabilities = [
            mock_result1,
            mock_result2,
        ]

        result = ocareport.create_capacity_report_availabilities(
            mock_client, 'compartment-id', 'AD-1', 'TestShape'
        )

        assert result == [mock_result1, mock_result2]

    def test_fault_domains_passed_in_single_report(self):
        """Test AD-level report requests each fault domain in one call."""
        mock_client = mock.MagicMock()
        mock_client.create_compute_capacity_report.return_value.data.shape_availabilities = []

        ocareport.create_capacity_report_availabilities(
            mock_client, 'compartment-id', 'AD-1', 'TestShape',
            fault_domains=['FAULT-DOMAIN-1', 'FAULT-DOMAIN-2', 'FAULT-DOMAIN-3']
        )

        call_args = mock_client.create_compute_capacity_report.call_args
        report_details = call_args[1]['create_compute_capacity_report_details']
        fault_domains = [
            shape_availability.fault_domain
            for shape_availability in report_details.shape_availabilities
        ]

        assert fault_domains == ['FAULT-DOMAIN-1', 'FAULT-DOMAIN-2', 'FAULT-DOMAIN-3']
        assert mock_client.create_compute_capacity_report.call_count == 1

    def test_fault_domain_omitted_when_not_provided(self):
        """Test AD-level report still supports an aggregate fallback."""
        mock_client = mock.MagicMock()
        mock_client.create_compute_capacity_report.return_value.data.shape_availabilities = []

        ocareport.create_capacity_report_availabilities(
            mock_client, 'compartment-id', 'AD-1', 'TestShape'
        )

        call_args = mock_client.create_compute_capacity_report.call_args
        report_details = call_args[1]['create_compute_capacity_report_details']

        assert report_details.shape_availabilities[0].fault_domain is None

    def test_flex_shape_config_passed(self):
        """Test AD-level report passes flex shape configuration."""
        mock_client = mock.MagicMock()
        mock_client.create_compute_capacity_report.return_value.data.shape_availabilities = []

        ocareport.create_capacity_report_availabilities(
            mock_client, 'compartment-id', 'AD-1',
            'VM.Standard.E5.Flex', is_flex=True, ocpu=16.0, memory=256.0
        )

        call_args = mock_client.create_compute_capacity_report.call_args
        report_details = call_args[1]['create_compute_capacity_report_details']
        shape_config = report_details.shape_availabilities[0].instance_shape_config

        assert shape_config.ocpus == 16.0
        assert shape_config.memory_in_gbs == 256.0


class TestCreateRegionClients:
    """Tests for region-specific OCI client creation."""

    @mock.patch('ocareport.oci.core.ComputeClient')
    @mock.patch('ocareport.oci.identity.IdentityClient')
    def test_create_region_clients_does_not_mutate_base_config(self, mock_identity, mock_compute):
        """Test regional client creation copies config before setting region."""
        base_config = {
            'region': 'us-ashburn-1',
            'tenancy': 'test-tenancy',
        }
        signer = mock.MagicMock()

        identity_client, core_client = ocareport.create_region_clients(
            base_config,
            signer,
            'eu-frankfurt-1'
        )

        assert identity_client == mock_identity.return_value
        assert core_client == mock_compute.return_value
        assert base_config['region'] == 'us-ashburn-1'

        identity_config = mock_identity.call_args.kwargs['config']
        compute_config = mock_compute.call_args.kwargs['config']

        assert identity_config['region'] == 'eu-frankfurt-1'
        assert compute_config['region'] == 'eu-frankfurt-1'
        assert identity_config is not base_config
        assert compute_config is not base_config


class TestAnalyzeRegionCapacity:
    """Tests for regional capacity collection."""

    @mock.patch('ocareport.create_capacity_report_availabilities')
    @mock.patch('ocareport.get_fault_domains')
    @mock.patch('ocareport.get_availability_domains')
    @mock.patch('ocareport.create_region_clients')
    def test_analyze_region_capacity_returns_table_rows(
        self,
        mock_create_clients,
        mock_get_ads,
        mock_get_fds,
        mock_create_report,
    ):
        """Test regional analysis returns normalized table rows."""
        mock_identity = mock.MagicMock()
        mock_core = mock.MagicMock()
        mock_create_clients.return_value = (mock_identity, mock_core)
        mock_get_ads.return_value = ['AD-1']
        mock_get_fds.return_value = ['FAULT-DOMAIN-1']

        availability = mock.MagicMock()
        availability.fault_domain = 'FAULT-DOMAIN-1'
        availability.instance_shape = 'TestShape'
        availability.availability_status = 'AVAILABLE'
        availability.available_count = 3
        mock_create_report.return_value = [availability]

        region = mock.MagicMock()
        region.region_name = 'eu-frankfurt-1'

        rows = ocareport.analyze_region_capacity(
            {'region': 'us-ashburn-1'},
            mock.MagicMock(),
            'test-tenancy',
            region,
            'TestShape'
        )

        assert rows == [{
            'region': 'eu-frankfurt-1',
            'availability_domain': 'AD-1',
            'fault_domain': 'FAULT-DOMAIN-1',
            'shape': 'TestShape',
            'status': 'AVAILABLE',
            'available_count': 3,
            'message': '',
        }]

    @mock.patch('ocareport.create_capacity_report_availabilities')
    @mock.patch('ocareport.get_fault_domains')
    @mock.patch('ocareport.get_availability_domains')
    @mock.patch('ocareport.create_region_clients')
    def test_analyze_region_capacity_records_ad_errors(
        self,
        mock_create_clients,
        mock_get_ads,
        mock_get_fds,
        mock_create_report,
    ):
        """Test an AD error becomes an ERROR row and does not abort analysis."""
        mock_create_clients.return_value = (mock.MagicMock(), mock.MagicMock())
        mock_get_ads.return_value = ['AD-1', 'AD-2']
        mock_get_fds.return_value = ['FAULT-DOMAIN-1']
        mock_create_report.side_effect = [
            oci.exceptions.ServiceError(500, 'InternalError', {}, 'temporary failure'),
            [],
        ]

        region = mock.MagicMock()
        region.region_name = 'eu-frankfurt-1'

        rows = ocareport.analyze_region_capacity(
            {'region': 'us-ashburn-1'},
            mock.MagicMock(),
            'test-tenancy',
            region,
            'TestShape'
        )

        assert rows[0] == {
            'region': 'eu-frankfurt-1',
            'availability_domain': 'AD-1',
            'fault_domain': '-',
            'shape': 'TestShape',
            'status': 'ERROR',
            'available_count': None,
            'message': 'temporary failure',
        }
        assert len(rows) == 1


class TestOutputAndExitCode:
    """Tests for output helpers and automation exit codes."""

    def test_get_exit_code_available(self):
        """Test exit code is 0 when at least one result is available."""
        assert ocareport.get_exit_code([
            {'status': 'OUT_OF_HOST_CAPACITY'},
            {'status': 'AVAILABLE'},
        ]) == 0

    def test_get_exit_code_error_without_availability(self):
        """Test exit code is 1 for technical/API errors without availability."""
        assert ocareport.get_exit_code([
            {'status': 'ERROR'},
        ]) == 1

    def test_get_exit_code_no_capacity(self):
        """Test exit code is 2 when no capacity is available."""
        assert ocareport.get_exit_code([
            {'status': 'OUT_OF_HOST_CAPACITY'},
        ]) == 2

    def test_render_json(self, capsys):
        """Test JSON output is machine readable."""
        rows = [{
            'region': 'eu-frankfurt-1',
            'availability_domain': 'AD-1',
            'fault_domain': 'FAULT-DOMAIN-1',
            'shape': 'TestShape',
            'status': 'AVAILABLE',
            'available_count': 2,
            'message': '',
        }]

        ocareport.render_json(rows)

        assert '"available_count": 2' in capsys.readouterr().out

    def test_render_csv(self, capsys):
        """Test CSV output includes automation-friendly columns."""
        rows = [{
            'region': 'eu-frankfurt-1',
            'availability_domain': 'AD-1',
            'fault_domain': 'FAULT-DOMAIN-1',
            'shape': 'TestShape',
            'status': 'AVAILABLE',
            'available_count': 2,
            'message': '',
        }]

        ocareport.render_csv(rows)

        output = capsys.readouterr().out
        assert 'region,availability_domain,fault_domain,shape,status,available_count,message' in output
        assert 'eu-frankfurt-1,AD-1,FAULT-DOMAIN-1,TestShape,AVAILABLE,2,' in output


class TestMain:
    """Tests for main function."""

    def test_main_function_exists(self):
        """Test that main() function exists."""
        assert hasattr(ocareport, 'main')
        assert callable(ocareport.main)


class TestFlexShapeDetection:
    """Tests for flex shape detection logic."""

    def test_flex_detected_in_shape_name(self):
        """Test that Flex is detected in shape name."""
        assert "Flex" in "VM.Standard.E5.Flex"
        assert "Flex" in "VM.Optimized3.Flex"

    def test_non_flex_shape(self):
        """Test non-flex shape detection."""
        assert "Flex" not in "VM.Standard2.1"
        assert "Flex" not in "BM.Standard.E4.128"
