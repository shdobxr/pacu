#!/usr/bin/env python3
import argparse
import boto3
from botocore.exceptions import ClientError
from functools import partial
import os
import time

from pacu import util


module_info = {
    # Name of the module (should be the same as the filename)
    'name': 'get_credential_report',

    # Name and any other notes about the author
    'author': 'Spencer Gietzen of Rhino Security Labs',

    # Category of the module. Make sure the name matches an existing category.
    'category': 'recon_enum_with_keys',

    # One liner description of the module functionality. This shows up when a user searches for modules.
    'one_liner': 'Generates and downloads an IAM credential report.',

    # Description about what the module does and how it works
    'description': 'This module tries to download a credential report for the AWS account, giving a lot of authentication history/info for users in the account. If it does not find a report, it will prompt you to generate one. The report is saved in ./sessions/[current_session_name]/downloads/get_credential_report_[current_time].csv',

    # A list of AWS services that the module utilizes during its execution
    'services': ['IAM'],

    # For prerequisite modules, try and see if any existing modules return the data that is required for your module before writing that code yourself, that way, session data can stay separated and modular.
    'prerequisite_modules': [],

    # Module arguments to autocomplete when the user hits tab
    'arguments_to_autocomplete': [],
}

parser = argparse.ArgumentParser(add_help=False, description=module_info['description'])


def help():
    return [module_info, parser.format_help()]


def main(args, database):
    session = util.get_active_session(database)

    ###### Don't modify these. They can be removed if you are not using the function.
    args = parser.parse_args(args)
    print = partial(util.print, session_name=session.name, database=database)
    input = partial(util.input, session_name=session.name, database=database)
    ######

    client = boto3.client(
        'iam',
        aws_access_key_id=session.access_key_id,
        aws_secret_access_key=session.secret_access_key,
        aws_session_token=session.session_token
    )

    report = None

    try:
        report = client.get_credential_report()

    except ClientError as error:
        report = None

        if error.response['Error']['Code'] == 'ReportNotPresent':
            generate = input('Credential report not generated, do you want to generate one? (y/n) ')

            if generate == 'y':
                response = client.generate_credential_report()
                print('Credential report generation started, this may take up to a couple minutes. Checking if it is ready every 20 seconds...')

                while report is None:
                    time.sleep(20)

                    try:
                        report = client.get_credential_report()
                    except ClientError as error:
                        if error.response['Error']['Code'] == 'ReportNotPresent':
                            report = None

    except:
        print('Download failed, you do not have the correct permissions to download a credential report.')
        return

    if 'Content' in report:
        if not os.path.exists(f'sessions/{session.name}/downloads'):
            os.makedirs(f'sessions/{session.name}/downloads')

        filename = f'sessions/{session.name}/downloads/get_credential_report_{time.time()}.csv'
        with open(filename, 'w+') as csv_file:
            csv_file.write(report['Content'].decode())

        print(f'Credential report saved to {filename}')

    print(f"{module_info['name']} completed.\n")
    return