import argparse
import pandas as pd
import json

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Convert CSV data to JSON")
parser.add_argument("input_csv", help="Input CSV file path")
parser.add_argument("--step_scale", type=float, default=4000, help="Scale factor for steps")
parser.add_argument("--loss_scale", type=float, default=1000, help="Scale factor for losses")
args = parser.parse_args()

# Read the CSV file
df = pd.read_csv(args.input_csv)

# Get the column names for all runs
run_columns = df.columns[1:]

with open("preset.json", "r") as preset_file:
    preset_data = json.load(preset_file)

# Process each run
for run_column in run_columns:
    # Convert columns to numeric
    df["Step"] = pd.to_numeric(df["Step"], errors="coerce")
    df[run_column] = pd.to_numeric(df[run_column], errors="coerce")

    # Find minimum and maximum values for scaling
    min_step = df["Step"].min()
    max_step = df["Step"].max()
    min_loss = df[run_column].min()
    max_loss = df[run_column].max()

    # Scale the data
    df["Step"] = (df["Step"] - min_step) / (max_step - min_step) * args.step_scale
    df[run_column] = (df[run_column] - min_loss) / (max_loss - min_loss) * args.loss_scale

    # Modify the column to ensure it increases
    df[run_column] = args.loss_scale - df[run_column]

    # Sort by step
    df = df.sort_values(by="Step")

    # Interpolate the data to increase the number of steps
    df = df.interpolate()

    # Ensure step ranges from 0 to step_scale
    df["Step"] = df["Step"].clip(0, args.step_scale)
    df[run_column] = df[run_column].clip(0, args.loss_scale)

    # Prepare JSON data
    json_data = {"lines": []}
    for i in range(len(df)):
        if i < len(df) - 1:
            line_data = {
                "id": i,
                "type": 0,
                "x1": df.iloc[i]["Step"],
                "y1": df.iloc[i][run_column],
                "x2": df.iloc[i + 1]["Step"],
                "y2": df.iloc[i + 1][run_column],
                "flipped": False,
                "leftExtended": False,
                "rightExtended": False
            }
        else:
            line_data = {
                "id": i,
                "type": 0,
                "x1": df.iloc[i]["Step"],
                "y1": df.iloc[i][run_column],
                "x2": args.step_scale,
                "y2": args.loss_scale,
                "flipped": False,
                "leftExtended": False,
                "rightExtended": False
            }
        json_data["lines"].append(line_data)

    # add json_data to preset_data
    preset_data["lines"] = json_data["lines"]

    # rename preset_data to merged_data 
    merged_data = preset_data


    # replace all spaces in run_column with underscores
    run_column = run_column.replace(" ", "_")
    # strip all forward slashes from run_column
    run_column = run_column.replace("/", "")
    # Write JSON data to file
    output_json = f"{run_column}.json"
    
    with open(output_json, "w") as json_file:
        json.dump(merged_data, json_file, indent=4)

    print(f"Output for {run_column} saved to {output_json}")
