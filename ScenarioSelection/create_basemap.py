import os
import re


def get_rasters(cdl_dir, cdl_format, select_region):
    rasters = []
    for f in os.listdir(cdl_dir):
        match = re.match(cdl_format, f)
        if match:
            region, year = match.groups()
            if region == select_region:
                rasters.append((int(year), os.path.join(cdl_dir, f)))
    return zip(*sorted(rasters))


def combine_rasters(rasters, _class):
    for i, raster in enumerate(rasters):
        print("\t{}".format(i))
        raster = (arcpy.Raster(raster) == _class)
        if not i:
            running = raster
        else:
            running += raster
    return running > 0


def main():
    classes = [1]
    regions = ['07']
    cdl_dir = os.path.join("..", "..", "aquatic-model-inputs", "bin", "Input", "CDL")
    cdl_format = re.compile("r(.+?)_(\d{4})\.img$")
    out_format = os.path.join("..", "bin", "Maps", "b{}_{}_{}_{}.img")

    for region in regions:
        years, rasters = get_rasters(cdl_dir, cdl_format, region)
        for _class in classes:
            combined = combine_rasters(rasters, _class)
            combined.save(out_format.format(region, _class, years[0], years[-1]))


if __name__ == "__main__":
    import arcpy

    main()
