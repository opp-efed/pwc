"""
Reads the PWC batch output file (usually Summary_SW.txt), creates percentiles for each scenario and selects a subset
based on a percentile and window
"""

import pandas as pd
import numpy as np

from paths import pwc_batch_file, pwc_summary_file, summary_outfile, selected_scenario_outfile

# This silences some error messages being raised by Pandas
pd.options.mode.chained_assignment = None


def compute_percentiles(scenario_table, test_fields):
    for field in test_fields:
        # Calculate percentiles
        data = scenario_table[['line_num', field, 'area']].sort_values(field).reset_index()
        weighted = ((np.cumsum(data.area) - 0.5 * data.area) / data.area.sum()) * 100
        unweighted = ((data.index + 1) / data.shape[0]) * 100

        # Add new columns to scenario table
        new_header = ["line_num", "{}_weighted_%ile".format(field), "{}_unweighted_%ile".format(field)]
        new_cols = pd.DataFrame(np.vstack((data.line_num, weighted, unweighted)).T, columns=new_header)
        scenario_table = scenario_table.merge(new_cols, on="line_num")

    return scenario_table


def read_pwc_output(in_file):
    # Read the table, manually entering in the header (original header is tough to parse)
    header = ['line_num', 'run_id', 'peak', '1-day', 'year', 'overall',
              '4-day', '21-day', '60-day', '90-day', 'pw_peak', 'pw_21']

    table = pd.read_csv(in_file, skiprows=1, names=header, delimiter='\s+')

    # Adjust line number by 2 so that header is not included
    table['line_num'] -= 2

    # Split the Batch Run ID field into constituent parts
    data = table.pop('run_id').str.split('_', expand=True)
    data.columns = ['run_id', 'scenario_id', 'rep']

    return pd.concat([data, table], axis=1)


def read_scenarios(scenario_table):
    scenarios = pd.read_csv(scenario_table, dtype={'area': np.int64})[
        ['scenario_id', 'state', 'soil_id', 'weather_grid', 'area']]
    scenarios['line_num'] = scenarios.index + 1
    return scenarios


def select_scenarios(scenarios, test_fields, selection_pct, window):
    keep_fields = ['duration', 'percentile', 'scenario_id_raw', 'state', 'soil_id', 'weather_grid', 'area', 'line_num',
                   'run_id', 'scenario_id_pwc']

    # Designate the lower and upper bounds for the percentile selection
    window /= 2  # half below, half above
    lower, upper = selection_pct - window, selection_pct + window

    # Select scenarios for each of the durations and combine
    all_selected = []
    for duration in test_fields:
        pct = "{}_weighted_%ile".format(duration)  # Percentile field for selection

        # Selects all scenarios within the window
        selection = scenarios[(scenarios[pct] >= lower) & (scenarios[pct] <= upper)]

        # Selects any scenarios outside the window with an equal value
        min_val, max_val = selection[duration].min(), selection[duration].max()
        selection = \
            scenarios[(scenarios[duration] >= min_val) & (scenarios[duration] >= max_val)]

        selection['duration'] = duration
        selection['percentile'] = selection[pct]
        all_selected.append(selection)
    all_selected = pd.concat(all_selected, axis=0)
    return all_selected.sort_values(['duration', 'area'], ascending=[True, False])[keep_fields]


def main():
    """ Set run parameters here """
    selection_pct = 90  # percentile for selection
    window = 0.1  # select scenarios within a range
    test_fields = \
        ['1-day', '4-day', '21-day', '60-day', '90-day', 'peak', 'year', 'overall']  # fields to compute percentiles on
    """"""""""""""""""""""""""""""

    # Join the scenarios data with the computed concentrations
    raw_scenarios = read_scenarios(pwc_batch_file)
    pwc_output = read_pwc_output(pwc_summary_file)
    scenarios = raw_scenarios.merge(pwc_output, on='line_num', how='left', suffixes=('_raw', '_pwc'))

    # Calculate percentiles for test fields and write to file
    scenarios = compute_percentiles(scenarios, test_fields)
    scenarios.to_csv(summary_outfile, index=None)

    # Select scenarios for each duration based on percentile, and write to file
    selection = select_scenarios(scenarios, test_fields, selection_pct, window)
    selection.to_csv(selected_scenario_outfile, index=None)


main()
