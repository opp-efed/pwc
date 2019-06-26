import pandas as pd
import os
import re

first_run = True


def find_files(file_dir, fmt):
    for f in os.listdir(file_dir):
        match = re.match(fmt, f)
        if match:
            region, cdl, cdl_name = match.groups()
            yield region, cdl, cdl_name, os.path.join(file_dir, f)


def take_sample(path, selection_pct, threshold):
    table = pd.read_csv(path)
    selection_size = max((threshold, int(table.shape[0] * (selection_pct / 100))))
    selection_size = min((selection_size, table.shape[0]))
    sample = table.sample(selection_size)
    return sample, sample.shape[0]


def record_stats(stats_file, size, region, cdl, name):
    global first_run
    if first_run:
        first_run = False
        os.remove(stats_file)
        with open(stats_file, 'w+') as f:
            f.write("cdl,cdl_name,region,n_scenarios\n")
    with open(stats_file, 'a') as f:
        f.write(",".join(map(str, (cdl, name, region, size))) + "\n")


def main():
    selection_pct = 25
    threshold = 1000
    infile_format = re.compile("r(.{2,3})_(\d{1,2})_(.+?).csv")
    scenario_dir = "E:/opp-efed/aquatic-model-inputs/bin/Production/PwcScenarios"
    selection_dir = os.path.join("Output", "Subsets")
    outfile_format = os.path.join(selection_dir, "r{}_{}_{}_sample.csv")
    summary_file = os.path.join(selection_dir, "selection_summary.csv")

    for region, cdl, name, path in find_files(scenario_dir, infile_format):
        sample, size = take_sample(path, selection_pct, threshold)
        sample.to_csv(outfile_format.format(region, cdl, name))
        record_stats(summary_file, size, region, cdl, name)
        print(region, cdl, size)

    # change around fields
    # plant begin -> plant active begin, etc
    # selections to sharepoint (nelson sent link)


main()
