import arcpy
import os
import pandas as pd
import re

from create_basemap import get_rasters

def process_rasters(rasters, summary, field, threshold):
    summary = summary[['scenario_id_raw', field]]
    for i, raster in enumerate(rasters):
        print("\t{}".format(i))
        raster = arcpy.Raster(raster)
        fields = [f.name for f in arcpy.ListFields(raster)]
        print(fields)
        exit()

        if not i:
            running = raster
        else:
            running += raster
    return running > 0

def get_fields(durations, weights):
    return ["{}_{}_%ile".format(d, w) for d in durations for w in weights]


def main():
    combo_dir = os.path.join("..", "..", "aquatic-model-inputs", "bin", "Intermediate", "CombinedRasters")
    combo_format = re.compile("c_(.{2,3})_(\d{4})$")
    summary_file = os.path.join("Output", "test_summary.csv")
    durations = ["1-day", "90-day"]
    weights = ["unweighted", "weighted"]
    regions = ['07']
    threshold = 90

    summary = pd.read_csv(summary_file)
    for region in regions:
        years, rasters = get_rasters(combo_dir, combo_format, region)
        for field in get_fields(durations, weights):
            print(region, field)
            combined = process_rasters(rasters, summary, field, threshold)
            combined.save(out_format.format(region, _class, years[0], years[-1]))


main()
