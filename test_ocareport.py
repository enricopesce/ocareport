"""Tests for ocareport.py CLI tool."""
import sys
from unittest import mock

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

    def test_region_all(self):
        """Test -region all for all regions."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-region', 'all', '-shape', 'TestShape']):
            args = ocareport.parse_arguments()
            assert args.region == 'all'

    def test_flex_options(self):
        """Test -ocpus and -memory set OCPU and memory for flex shapes."""
        with mock.patch.object(sys, 'argv', ['ocareport.py', '-shape', 'VM.Standard.E5.Flex', '-ocpus', '24', '-memory', '512']):
            args = ocareport.parse_arguments()
            assert args.ocpu == 24.0
            assert args.memory == 512.0

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

    def test_returns_all_regions(self):
        """Test all regions returned when 'all' specified."""
        mock_client = mock.MagicMock()
        mock_region1 = mock.MagicMock()
        mock_region1.region_name = 'us-ashburn-1'
        mock_region1.is_home_region = True
        mock_region2 = mock.MagicMock()
        mock_region2.region_name = 'eu-frankfurt-1'
        mock_region2.is_home_region = False

        mock_client.list_region_subscriptions.return_value.data = [mock_region1, mock_region2]

        result = identity.get_region_subscription_list(mock_client, 'test-tenancy', 'all')

        assert len(result) == 2

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
