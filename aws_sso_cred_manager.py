import os
import sys
import time
from pathlib import Path
import argparse
import subprocess
import configparser
import boto3
from botocore.session import Session

# Set the default paths
DEFAULT_CONFIG_FILE_PATH = '~/.aws/config'
DEFAULT_CREDENTIALS_FILE_PATH = '~/.aws/credentials'

# Get the environment variables or use the default paths
CONFIG_FILE_PATH = os.getenv('AWS_CONFIG_FILE', DEFAULT_CONFIG_FILE_PATH)
CREDENTIALS_FILE_PATH = os.getenv('AWS_SHARED_CREDENTIALS_FILE', DEFAULT_CREDENTIALS_FILE_PATH)


class AWSSSOManager:
    def __init__(self):
        self.profile = None

    def verify_profile_exists(self):
        # Get the path to the AWS config file
        config_file = Path(CONFIG_FILE_PATH).expanduser()

        # Read the existing config file
        config = configparser.ConfigParser()
        config.read(config_file)

        # Check if the specified profile exists
        if not config.has_section(f'profile {self.profile}'):
            raise ValueError(f"Profile '{self.profile}' does not exist in the AWS config file")

    def get_sso_credentials(self, retry_count=0):
        try:
            # Create a session and SSO client
            _session = Session(profile=self.profile)
            sso = boto3.client('sso')

            # Retrieve the SSO credentials
            creds = sso._request_signer._credentials
            return creds.access_key, creds.secret_key, creds.token
        except Exception as e:
            if retry_count < 3 and "Token has expired and refresh failed" in str(e):
                print("Token has expired. Refreshing token...")
                self.refresh_sso_token()
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self.get_sso_credentials(retry_count + 1)
            else:
                print(f"Failed to retrieve SSO credentials: {e}")
                sys.exit(1)

    def refresh_sso_token(self):
        try:
            subprocess.run(['aws', 'sso', 'login', '--profile', self.profile], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to refresh SSO token: {e}")
            sys.exit(1)

    def update_credentials_file(self, access_key, secret_key, session_token):
        try:
            # Get the path to the AWS credentials file
            cred_file = Path(CREDENTIALS_FILE_PATH).expanduser()

            # Read the existing credentials file
            config = configparser.ConfigParser()
            config.read(cred_file)

            # Remove the existing profile section if it exists
            if config.has_section(self.profile):
                config.remove_section(self.profile)

            # Add the new profile section with the SSO credentials
            config.add_section(self.profile)
            config[self.profile]['aws_access_key_id'] = access_key
            config[self.profile]['aws_secret_access_key'] = secret_key
            config[self.profile]['aws_session_token'] = session_token

            # Write the updated credentials file
            with open(cred_file, 'w') as f:
                config.write(f)

        except Exception as e:
            # Handle the exception here
            print(f"An error occurred when refreshing credentials: {str(e)}")

        # Update complete
        print(f"Access token refreshed successfully")

    def configure_sso(self):
        try:
            subprocess.run(['aws', 'configure', 'sso'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to configure SSO: {e}")
            sys.exit(1)

    def run(self):
        if self.profile:
            # Verify the profile exists
            self.verify_profile_exists()

            # Get the SSO credentials
            access_key, secret_key, session_token = self.get_sso_credentials()

            # Update the AWS credentials file with the SSO credentials
            self.update_credentials_file(access_key, secret_key, session_token)
        else:
            # Configure SSO
            self.configure_sso()


# Create the argparser object
parser = argparse.ArgumentParser(description='AWS SSO Credential Manager')
parser.add_argument('-p', '--profile', help='AWS profile name')
parser.add_argument('-c', '--configure', help='Configure SSO', action='store_true')


def parse_arguments():
    return parser.parse_args()


if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()

    # Instantiate the AWSSSOManager
    sso_manager = AWSSSOManager()

    # Switch case to handle different options
    if args.configure:
        # Configure SSO
        sso_manager.configure_sso()
    elif args.profile:
        # Set the profile and refresh credentials
        sso_manager.profile = args.profile
        sso_manager.run()
    else:
        # Print help message
        parser.print_help()
