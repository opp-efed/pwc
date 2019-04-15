import os
import re
import pandas as pd
import datetime as dt
import numpy as np


def area_under_curve(table, field):
    return table[field].sum(), np.trapz(table[field])


def find_files(file_dir, file_format, run_filter=None, scenario_filter=None):
    for f in os.listdir(file_dir):
        match = re.match(file_format, f)
        if match:
            run_id, scenario_id = match.groups()
            if (scenario_filter is None or scenario_id in scenario_filter) and \
                    (run_filter is None or run_id in run_filter):
                yield scenario_id, os.path.join(file_dir, f)


def read_file(path, header):
    table = pd.read_csv(path, skiprows=5, names=header)
    with open(path) as f:
        line = [next(f) for _ in range(5)][-1]
    days_since_1900 = int(re.search("(\d+?) = Start Day", line).group(1))
    start_date = dt.datetime(1900, 1, 1) + dt.timedelta(days=days_since_1900)
    table['date'] = pd.date_range(start_date, periods=table.shape[0])
    return table.set_index('date')


def write_to_file(table, outfile, header):
    pd.DataFrame(table, columns=header).to_csv(outfile, index=None)


def main():
    out_file = "Output/test_table.csv"
    time_series_dir = "E:/PWC/777e"
    file_format = re.compile("(.+?)_(.+?)_Pond_Parent_daily.csv")
    infile_header = ['depth', 'wc_conc', 'benthic_conc', 'peak_wc_conc']
    outfile_header = ['scenario_id', 'aoc_sum', 'aoc_trapezoid']

    # Initialize output table
    summary_table = []

    # Loop through all files in directory, apply filter if needed
    for scenario_id, file in find_files(time_series_dir, file_format):

        # Read the input file
        table = read_file(file, infile_header)

        # Calculate area under curve
        aoc_sum, aoc_trapezoid = area_under_curve(table, 'wc_conc')

        # Add summary results to output table
        summary_table.append([scenario_id, aoc_sum, aoc_trapezoid])

    # Write the summary table to output file
    write_to_file(summary_table, out_file, outfile_header)


main()
