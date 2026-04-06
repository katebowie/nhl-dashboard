import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import glob

csv_files = glob.glob("bigdatacup_2026/*.csv")
csv_files = [
    f for f in csv_files
    if "camera_orientations" not in f
]

dfs = [pd.read_csv(f) for f in csv_files]
tracking = pd.concat(dfs, ignore_index=True)