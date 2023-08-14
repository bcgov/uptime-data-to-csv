import argparse
from dateutil import parser
from datetime import timedelta, datetime
import csv
import re
import time
import requests

CONFIG = {
    'api': 'https://uptime.com/api/v1/',
    'token': '',
    'headers': {}
}

CHECK_NAMES = {}
EST_CALLS = 0
UPTIME_MAX_RPM = 60
DEFAULT_DAYS = 30


def parse_date(d):
    return parser.parse(d)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download stats in bulk for all checks.')
    parser.add_argument('-t', '--token', required=True,
                        help='Your Uptime.com API Token')
    parser.add_argument('-pk', '--check_pk', required=True,
                        help='Primary key of the checks you would like to pull data from. If supplying multiple keys, separate with a comma. Eg: 147,789')
    parser.add_argument('-d', '--date', type=parse_date,
                        help='(optional) Date to end saving statistics from, in ISO 8601 format. If not supplied, will use current date.')
    parser.add_argument('-n', '--num_days',
                        help='(optional) Number of days to fetch data from "--date". Default is %s.' % DEFAULT_DAYS)
    parser.add_argument('-o', '--output',
                        help='(optional) Specify type of data to output (response_time, alerts, etc.)')
    parser.add_argument('--api',
                        help='(optional) The Uptime.com API endpoint to use, eg. '
                             'https://uptime.com/api/v1/')

    return parser.parse_args()


def make_api_call(label, method, endpoint, pk=None, params=None, json=None, slow_down=False):
    """Make an Uptime.com API call with the given method, endpoint and parameters."""
    url = CONFIG['api'] + endpoint.format(pk=pk)

    if slow_down:
        time.sleep(1.05)

    r = requests.request(method, url, params=params,
                         json=json, headers=CONFIG['headers'])
    r.raise_for_status()
    return r.json()


def load_all_checks_stats(from_date, check_pk, days):
    """Load info and stats for all checks in the account, spanning multiple pages
    of results if necessary."""
    global EST_CALLS

    stats = []

    check_pks = check_pk.split(',')
    days = DEFAULT_DAYS if not days else int(days)
    # If no pk specified, will return data for all checks. Will want to apply request slow down.
    EST_CALLS = "> 60" if not check_pk else len(
        check_pks) + len(check_pks) * (days + 1)

    print("Est. number of calls: %s" % EST_CALLS)
    slow_down = True if not check_pk else EST_CALLS > UPTIME_MAX_RPM
    if slow_down:
        print("Est. number of calls exceeds Uptime rate limit of %s req/min. Request slow down will occur." % UPTIME_MAX_RPM)
    else:
        print("Request slowdown will NOT occur.")

    for cpk in check_pk.split(','):
        print("Fetching data for check with primary key: %s ..." % cpk)
        current_date = from_date - \
            timedelta(
                days=days)
        termination_date = from_date + timedelta(days=1)
        r = make_api_call("Get check name", 'get', 'checks/%s' %
                          cpk, slow_down=slow_down)
        CHECK_NAMES[cpk] = r['name']

        while current_date != termination_date:
            r = make_api_call('Reading check stats',
                              'get', 'checks/bulk/stats/',
                              params={'pk': cpk,
                                      'start_date': current_date.strftime("%Y-%m-%d"),
                                      'end_date': current_date.strftime("%Y-%m-%d"),
                                      'include_alerts': '1'}, slow_down=slow_down)
            stats.append(r['checks'])
            current_date = current_date + timedelta(days=1)

    return stats


def output_res_time_csv(stats):
    csv_file = "response_time.csv"
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)

        writer.writerow(["checkPK", "checkName", "dateTime", "responseTime"])

        for stat in stats:
            for entry in stat:
                pk = entry["pk"]
                check_name = CHECK_NAMES.get(str(pk), '')
                for stats in entry["statistics"]:
                    for datapoint in stats["response_time_datapoints"]:
                        dateTime, responseTime = datapoint
                        writer.writerow(
                            [pk, check_name, dateTime, responseTime])


def output_alerts_csv(stats):
    csv_file = "alerts.csv"
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)

        writer.writerow(["alertPK", "checkPK", "checkName", "createdAt",
                        "endedAt", "stateIsUp", "ignored", "durationSecs", "output"])

        for stat in stats:
            for entry in stat:
                check_pk = entry["pk"]
                check_name = CHECK_NAMES.get(str(check_pk), '')
                for stats in entry["statistics"]:
                    for alert in stats["alerts"]:
                        writer.writerow([alert["pk"], check_pk, check_name, alert["created_at"], alert["ended_at"],
                                        alert["state_is_up"], alert["ignored"], alert["duration_secs"], re.sub(r'\s+', ' ', alert["output"])])


def main():
    """Program entry point."""

    print("WARNING: Uptime API has a rate limit of 60 calls per minute. If more than 60 calls are required, a delay will be placed in an attempt to comply with this limit.")

    opts = parse_args()
    CONFIG['api'] = opts.api or CONFIG['api']
    CONFIG['headers'] = {'Authorization': 'token ' + opts.token}

    date = opts.date if opts.date else datetime.today()
    stats = load_all_checks_stats(date, opts.check_pk, opts.num_days)

    output_types = [] if not opts.output else opts.output.split(',')

    if not opts.output or 'response_time' in output_types:
        output_res_time_csv(stats)
    if not opts.output or 'alerts' in output_types:
        output_alerts_csv(stats)


if __name__ == '__main__':
    main()
