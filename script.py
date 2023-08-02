import argparse
import datetime as dt
import json
from datetime import timedelta

import requests

CONFIG = {
    'api': 'https://uptime.com/api/v1/',
    'token': '',
    'headers': {},
}


def parse_date(d):
    return dt.datetime.strptime(d, '%Y-%m-%d').date()


def parse_args():
    parser = argparse.ArgumentParser(description='Download stats in bulk for all checks.')
    parser.add_argument('--token', required=True,
                        help='Your Uptime.com API Token')
    parser.add_argument('--api',
                        help='(optional) The Uptime.com API endpoint to use, eg. '
                             'https://uptime.com/api/v1/')
    parser.add_argument('-d', '--date', required=True, type=parse_date,
                        help='Date to end saving statistics from, YYYY-MM-DD')

    return parser.parse_args()


def make_api_call(label, method, endpoint, pk=None, params=None, json=None):
    """Make an Uptime.com API call with the given method, endpoint and parameters."""
    url = CONFIG['api'] + endpoint.format(pk=pk)

    r = requests.request(method, url, params=params, json=json, headers=CONFIG['headers'])
    r.raise_for_status()
    return r.json()


def load_all_checks_stats(from_date):
    """Load info and stats for all checks in the account, spanning multiple pages
    of results if necessary."""
    current_date = from_date - timedelta(days=3) #CHANGE TO 30 DAYS, SET TO 3 FOR QUICKER TESTING
    termination_date = from_date + timedelta(days=1)
    stats = []

    while current_date != termination_date:
        r = make_api_call('Reading check stats',
                          'get', 'checks/bulk/stats/',
                          params={'pk': '1389736',
                                  'start_date': str(current_date),
                                  'end_date': str(current_date),
                                  'include_alerts': '1'})
        stats.append(r['checks'])
        current_date = current_date + timedelta(days=1)

    return stats


def main():
    """Program entry point."""
    opts = parse_args()
    CONFIG['api'] = opts.api or CONFIG['api']
    CONFIG['headers'] = {'Authorization': 'token ' + opts.token}

    stats = load_all_checks_stats(opts.date)
    print(json.dumps(stats, indent=4))


if __name__ == '__main__':
    main()