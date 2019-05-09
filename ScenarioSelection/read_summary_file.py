import os
import pandas as pd
import numpy as np

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
    window /= 2
    lower, upper = selection_pct - window, selection_pct + window
    all_selected = None
    for duration in test_fields:
        field = "{}_weighted_%ile".format(duration)
        selection = scenarios[(scenarios[field] >= lower) & (scenarios[field] <= upper)]
        selection['duration'] = duration
        selection['percentile'] = selection[field]
        all_selected = selection if all_selected is None else pd.concat([all_selected, selection], axis=0)
    all_selected['dev'] = all_selected.percentile - selection_pct
    return all_selected.sort_values(['duration', 'dev'])[keep_fields]


def main():
    """ Set run parameters here """
    scenario_table = os.path.join("Input", "Samples", "corn_60k.csv")  # the table used as input for the pwc run
    summary_file = os.path.join("Input", "Samples", "Summary_SW_60k.txt")  # the output file from the pwc run
    output_dir = "Output"  # where output data will be written
    summary_output = os.path.join(output_dir, "test_summary2.csv")
    selection_output = os.path.join(output_dir, "test_selection2.csv")
    selection_pct = 90  # percentile for selection
    window = 0.1  # select scenarios within a range
    test_fields = \
        ['1-day', '4-day', '21-day', '60-day', '90-day', 'peak', 'year', 'overall']  # fields to compute percentiles on
    """"""""""""""""""""""""""""""

    # Join the scenarios data with the computed concentrations
    raw_scenarios = read_scenarios(scenario_table)
    pwc_output = read_pwc_output(summary_file)
    scenarios = raw_scenarios.merge(pwc_output, on='line_num', how='left', suffixes=('_raw', '_pwc'))

    # Calculate percentiles for test fields and write to file
    scenarios = compute_percentiles(scenarios, test_fields)
    scenarios.to_csv(summary_output, index=None)

    # Select scenarios for each duration based on percentile, and write to file
    selection = select_scenarios(scenarios, test_fields, selection_pct, window)
    selection.to_csv(selection_output, index=None)
    print("Done")

main()
