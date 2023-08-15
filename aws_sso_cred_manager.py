import os
import sys
import time
from pathlib import Path
import argparse
import subprocess
import configparser
import boto3
from botocore.session import Session

class AWSSSOManager:
    def __init__(self, profile):
        self.profile = profile

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
        # Get the path to the AWS credentials file
        cred_file = Path('~/.aws/credentials').expanduser()

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

    def run(self):
        # Get the SSO credentials
        access_key, secret_key, session_token = self.get_sso_credentials()

        # Update the AWS credentials file with the SSO credentials
        self.update_credentials_file(access_key, secret_key, session_token)

def parse_arguments():
    parser = argparse.ArgumentParser(description='AWS SSO Credential Manager')
    parser.add_argument('-p', '--profile', help='AWS profile name', required=True)
    return parser.parse_args()

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    profile = args.profile

    # Instantiate the AWSSSOManager and run the process
    sso_manager = AWSSSOManager(profile)
    sso_manager.run()
