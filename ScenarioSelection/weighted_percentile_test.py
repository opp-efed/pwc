import os
import numpy as np

from read_summary_file import read_scenarios, read_pwc_output


def weighted_percentile_test(table, sample_size=1000, test_field='year'):
    table = table.iloc[:sample_size]
    table.area = table.area.floordiv(900 * 900)  # inflated area to real area to pixels

    # Brute force
    areas = table[['line_num', 'area']]
    vals = (areas.loc[areas.index.repeat(areas.area)]
            .merge(table[['line_num', test_field]], on='line_num')
            .sort_values(test_field).reset_index())
    vals['percentile'] = (vals.index / vals.shape[0]) * 100
    results = vals[['line_num', 'percentile']].groupby('line_num').describe()
    results.columns = results.columns.get_level_values(1)
    brute_results = results[['min', 'max', 'mean']].reset_index()

    # Weighted sampling
    weighted = table[['line_num', test_field, 'area']].sort_values(test_field)
    weighted['weighted_percentile'] = ((np.cumsum(weighted.area) - 0.5 * weighted.area) / weighted.area.sum()) * 100

    # Summary
    summary = brute_results.merge(weighted[['line_num', 'weighted_percentile']], on='line_num', how='left')
    return summary


def main():
    """ Set run parameters here """
    scenario_table = os.path.join("Input", "Samples", "corn_60k.csv")  # the table used as input for the pwc run
    summary_file = os.path.join("Input", "Samples", "Summary_SW_60k.txt")  # the output file from the pwc run
    output_dir = "Output"  # where output data will be written
    """"""""""""""""""""""""""""""

    # Join the scenarios data with the computed concentrations
    raw_scenarios = read_scenarios(scenario_table)
    pwc_output = read_pwc_output(summary_file)
    scenarios = raw_scenarios.merge(pwc_output, on='line_num', how='left', suffixes=('_raw', '_pwc'))

    summary = weighted_percentile_test(scenarios)
    summary.to_csv(os.path.join(output_dir, "comparison.csv"))


main()
