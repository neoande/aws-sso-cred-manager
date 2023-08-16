# AWS SSO Credential Manager

The AWS SSO Credential Manager is a Python script that helps manage AWS Single Sign-On (SSO) credentials by retrieving and updating them in the AWS credentials file.

## Installation

To use the AWS SSO Credential Manager, you can clone the repository from GitHub:

```bash
git clone https://github.com/neoande/aws-sso-cred-manager.git
```
## Usage
To use the AWS SSO Credential Manager, navigate to the cloned repository directory:

```bash
cd aws-sso-credential-manager
```
### Then, run the setup_env.py script with the desired AWS profile name as an argument:

```bash
python3 aws_sso_cred_manager.py -p <profile_name>
```
### For example, to manage the credentials for the my-profile AWS profile:

```bash
python3 aws_sso_cred_manager.py -p my-profile
```

The script will retrieve the SSO credentials for the specified profile and update the AWS credentials file (`~/.aws/credentials`) with the new credentials.

Suppose the SSO token has expired and refresh failed. In that case, the script will automatically perform an AWS SSO login for the profile and retry the retrieval of credentials with exponential backoff for a maximum of 3 attempts.

## Dependencies

The AWS SSO Credential Manager requires the following dependencies:

- boto3
- botocore

You can install these dependencies using pip:

```bash
pip3 install boto3 botocore
```

## Author
This project was created by [Nishant Tyagi](https://github.com/neoande)

## License

This project is licensed under the MIT License. See the LICENSE file for details.
