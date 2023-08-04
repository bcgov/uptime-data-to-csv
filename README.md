# Uptime.com Data to CSV

## Purpose

Fetches data from Uptime.com and outputs to a .csv file.

## Uptime Check Primary Keys

This script requires you to supply primary keys of the checks you would like to retrieve data for. In order to view primary keys:
- Go to one of the Uptime status pages ([prod](https://uptime.com/statuspage/bcgov-dss), or [non-prod](https://uptime.com/statuspage/bcgov-dss-nonprod)), select a check, and copy the primary key from the end of the URL.
- From the Uptime dashboard, select a check, and copy primary key from end of the URL.

> **Info**
> You can supply multiple primary keys by separating keys by a comma. Eg: `-pk 13896,16934`

## Usage

To view available options, run:

```sh
python3 script.py -h
```

You must first save an Uptime API token as an environment variable:

```sh
export TOK="" # Uptime API Token
```

Then run:

```sh
# Get check data from today's date, going back in time by the default amount
python3 script.py -t $TOK -pk 1389736 -d $(date +"%Y-%m-%d")
```

### Other Samples

```sh
# Get check data for the check with pk 1389736
python3 script.py -t $TOK -pk 1389736

# Get check data for check starting on 2023-07-23 (note: this check may fail if running in the future.)
python3 script.py -t $TOK -pk 1389736 -d "2023-07-23"

# Get check data from today's date, fetching data from 10 days back:
python3 script.py -t $TOK -pk 1389736 -n 10

# Get check data from multiple checks:
python3 script.py -t $TOK -pk 1389736,1662934

# Output a csv for alert data only:
python3 script.py -t $TOK -pk 1389736 -o alerts
```