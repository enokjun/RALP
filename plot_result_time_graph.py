"""
Plot output variable(s) vs time for a specific (X, Y) grid point from 3DTSP results.

Usage:
    python plot_result_time_graph.py <results_json> <x> <y> [variable1] [variable2] ...

    If no variables are specified, lists all available time-stepped variables.

Examples:
    # List available variables:
    python plot_result_time_graph.py "./04-Results/project_filename - all_input_results.json" 50 50

    # Plot min_FS vs time at (50, 50):
    python plot_result_time_graph.py "./04-Results/project_filename - all_input_results.json" 50 50 min_FS

    # Plot multiple variables at (50, 50):
    python plot_result_time_graph.py "./04-Results/project_filename - all_input_results.json" 50 50 min_FS gwt_dz z_w

    # Specify iteration (default=1):
    python plot_result_time_graph.py "./04-Results/project_filename - all_input_results.json" 50 50 min_FS --iteration 2

    # Plot probabilistic results:
    python plot_result_time_graph.py "./04-Results/project_filename - all_input_results.json" 50 50 prob_susceptibility_landslide prob_susceptibility_debris_flow
"""

import sys
import os
import json
import argparse
import numpy as np
from plotly.offline import plot as plotly_offline_plot
import plotly.graph_objs as go


def load_results_json(json_path):
    """Load the all_input_results.json file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def get_time_stepped_variables(results_dict, iteration_str="1"):
    """Identify all time-stepped variables available in the results.
    
    Returns dict of {variable_name: {time_step_str: [folder, filename, ...], ...}}
    """
    time_stepped_vars = {}
    iter_data = results_dict["iterations"].get(iteration_str, {})

    # Check iteration-level variables that have time-stepped sub-dictionaries
    for key, value in iter_data.items():
        if isinstance(value, dict):
            # Check if sub-keys are numeric strings (time step indices)
            sub_keys = list(value.keys())
            if len(sub_keys) > 0 and all(k.isdigit() for k in sub_keys):
                # Verify entries contain file path info (list with folder + filename)
                sample = value[sub_keys[0]]
                if isinstance(sample, list) and len(sample) >= 2 and isinstance(sample[0], str):
                    time_stepped_vars[key] = value

    return time_stepped_vars


def get_probabilistic_variables(results_dict):
    """Identify probabilistic time-stepped variables.
    
    Returns dict of {variable_name: {time_step_str: [folder, filename], ...}}
    """
    prob_vars = {}
    for key in ["probabilistic_landslide", "probabilistic_debris_flow"]:
        if key in results_dict:
            value = results_dict[key]
            if isinstance(value, dict):
                sub_keys = [k for k in value.keys() if k.isdigit()]
                if len(sub_keys) > 0:
                    # Remap to user-friendly names
                    friendly_name = key.replace("probabilistic_", "prob_susceptibility_")
                    prob_vars[friendly_name] = {k: v for k, v in value.items() if k.isdigit()}
    return prob_vars


def read_gis_file(filepath):
    """Read a GIS result file (CSV, ASC, or GRD) and return as Nx3 XYZ numpy array."""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.csv':
        return np.loadtxt(filepath, delimiter=',')
    
    elif ext == '.asc':
        # ESRI ASCII grid format
        meta = {}
        header_lines = 0
        with open(filepath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2 and not parts[0].replace('.','',1).replace('-','',1).replace('+','',1).isdigit():
                    meta[parts[0].lower()] = parts[1]
                    header_lines += 1
                else:
                    break
        
        ncols = int(meta['ncols'])
        nrows = int(meta['nrows'])
        xllcorner = float(meta.get('xllcorner', meta.get('xllcenter', 0)))
        yllcorner = float(meta.get('yllcorner', meta.get('yllcenter', 0)))
        cellsize = float(meta['cellsize'])
        nodata = float(meta.get('nodata_value', meta.get('nodata', -9999)))
        
        data = np.loadtxt(filepath, skiprows=header_lines)
        
        # Convert grid to XYZ
        xyz_list = []
        for row_i in range(nrows):
            for col_j in range(ncols):
                x = xllcorner + col_j * cellsize
                y = yllcorner + (nrows - 1 - row_i) * cellsize
                z = data[row_i, col_j]
                xyz_list.append([x, y, z])
        return np.array(xyz_list)
    
    elif ext == '.grd':
        # Surfer GRD text format
        with open(filepath, 'r') as f:
            lines = f.readlines()
        # line 0: "DSAA"
        # line 1: ncols nrows
        # line 2: xmin xmax
        # line 3: ymin ymax
        # line 4: zmin zmax
        ncols, nrows = int(lines[1].split()[0]), int(lines[1].split()[1])
        xmin, xmax = float(lines[2].split()[0]), float(lines[2].split()[1])
        ymin, ymax = float(lines[3].split()[0]), float(lines[3].split()[1])
        
        dx = (xmax - xmin) / (ncols - 1) if ncols > 1 else 0
        dy = (ymax - ymin) / (nrows - 1) if nrows > 1 else 0
        
        data_lines = lines[5:]
        values = []
        for line in data_lines:
            values.extend([float(v) for v in line.split()])
        
        xyz_list = []
        idx = 0
        for row_i in range(nrows):
            for col_j in range(ncols):
                x = xmin + col_j * dx
                y = ymin + row_i * dy
                z = values[idx]
                idx += 1
                xyz_list.append([x, y, z])
        return np.array(xyz_list)
    
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def find_nearest_grid_point(xyz_data, target_x, target_y):
    """Find the row in xyz_data closest to (target_x, target_y) and return its value.
    
    Returns (matched_x, matched_y, value) or (None, None, None) if not found.
    """
    distances = (xyz_data[:, 0] - target_x)**2 + (xyz_data[:, 1] - target_y)**2
    idx = np.argmin(distances)
    return xyz_data[idx, 0], xyz_data[idx, 1], xyz_data[idx, 2]


def compute_time_values(results_dict):
    """Compute actual time values for each time step from the rainfall history.
    
    Returns (time_values_in_user_units, time_unit_label, dt_seconds, convert_time)
    """
    original_input = results_dict.get("original_input", {})
    rainfall_history = original_input.get("rainfall_history", [])
    dt_iteration = original_input.get("dt_iteration", 1)
    rain_unit = original_input.get("rain_unit", "mm/hr")

    # Parse time unit
    parts = rain_unit.split("/")
    time_unit = parts[1] if len(parts) > 1 else "hr"

    convert_time = 1
    if time_unit == "hr":
        convert_time = 3600
        time_unit_label = "hr"
    elif time_unit == "min":
        convert_time = 60
        time_unit_label = "min"
    else:
        time_unit_label = "s"

    if len(rainfall_history) == 0:
        return [], time_unit_label, 0, convert_time

    # Compute dt in user time units
    dt = min(abs(e - s) for (s, e, *_) in rainfall_history) / dt_iteration

    # Build time step values (in user units): t0=0, t1=dt, t2=2*dt, ...
    total_duration = max(e for (_, e, *_) in rainfall_history) - min(s for (s, *_) in rainfall_history)
    num_steps = int(round(total_duration / dt))

    start_time = min(s for (s, *_) in rainfall_history)
    time_values = [start_time + i * dt for i in range(num_steps + 1)]

    return time_values, time_unit_label, dt * convert_time, convert_time


def extract_time_series(var_file_dict, target_x, target_y):
    """Extract value at (target_x, target_y) for each time step.
    
    Returns (time_step_indices, values, matched_x, matched_y)
    """
    time_steps = sorted(var_file_dict.keys(), key=int)
    indices = []
    values = []
    matched_x = None
    matched_y = None

    for ts in time_steps:
        file_info = var_file_dict[ts]
        folder = file_info[0]
        filename = file_info[1]
        filepath = os.path.join(folder, filename)

        if not os.path.exists(filepath):
            print(f"  Warning: File not found: {filepath}, skipping time step {ts}")
            continue

        xyz_data = read_gis_file(filepath)
        mx, my, val = find_nearest_grid_point(xyz_data, target_x, target_y)
        matched_x = mx
        matched_y = my
        indices.append(int(ts))
        values.append(val)

    return indices, values, matched_x, matched_y


def plot_time_graph(plot_data, time_values, time_unit_label, target_x, target_y, 
                    matched_x, matched_y, output_path, open_html=False):
    """Generate a plotly interactive line graph of variable(s) vs time.
    
    Args:
        plot_data: list of (variable_name, time_indices, values)
        time_values: list of actual time values in user units
        time_unit_label: string label for time unit
        target_x, target_y: requested coordinates
        matched_x, matched_y: actual grid coordinates used
        output_path: path for the output HTML file
        open_html: whether to open in browser
    """
    traces = []
    color_list = [
        'rgba(31, 119, 180, 1)',   # blue
        'rgba(255, 127, 14, 1)',   # orange
        'rgba(44, 160, 44, 1)',    # green
        'rgba(214, 39, 40, 1)',    # red
        'rgba(148, 103, 189, 1)',  # purple
        'rgba(140, 86, 75, 1)',    # brown
        'rgba(227, 119, 194, 1)',  # pink
        'rgba(127, 127, 127, 1)',  # gray
        'rgba(188, 189, 34, 1)',   # olive
        'rgba(23, 190, 207, 1)',   # cyan
    ]

    # Determine if we have a single variable or multiple
    single_var = len(plot_data) == 1

    for i, (var_name, time_indices, values) in enumerate(plot_data):
        # Map time step indices to actual time values
        if len(time_values) > 0:
            x_vals = [time_values[ti] if ti < len(time_values) else ti for ti in time_indices]
        else:
            x_vals = time_indices

        color = color_list[i % len(color_list)]
        trace = go.Scatter(
            x=x_vals,
            y=values,
            mode='lines+markers',
            name=var_name,
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color),
            hovertemplate=f'{var_name}<br>Time: %{{x:.2f}} {time_unit_label}<br>Value: %{{y:.5g}}<extra></extra>'
        )
        traces.append(trace)

    # Y-axis label
    if single_var:
        y_label = plot_data[0][0]
    else:
        y_label = "Value"

    coord_info = f"at ({matched_x}, {matched_y})"
    if matched_x != target_x or matched_y != target_y:
        coord_info += f"  [requested ({target_x}, {target_y})]"

    layout = go.Layout(
        title=f"Results vs Time {coord_info}",
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(255,255,255,1)',
        xaxis=dict(
            title=f'Time [{time_unit_label}]',
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=True,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.5)',
        ),
        yaxis=dict(
            title=y_label,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=True,
            showgrid=True,
            gridcolor='rgba(200,200,200,0.5)',
        ),
        showlegend=not single_var,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=65, r=50, b=65, t=90),
        hovermode='closest',
    )

    fig = go.Figure(data=traces, layout=layout)
    plotly_offline_plot(fig, filename=output_path, auto_open=open_html)
    print(f"Plot saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Plot output variable(s) vs time for a specific (X, Y) grid point from 3DTSP results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("results_json", help="Path to the 'all_input_results.json' file")
    parser.add_argument("x", type=float, help="X coordinate of the grid point")
    parser.add_argument("y", type=float, help="Y coordinate of the grid point")
    parser.add_argument("variables", nargs='*', help="Variable name(s) to plot. If omitted, lists available variables.")
    parser.add_argument("--iteration", "-i", type=int, default=1, help="Monte Carlo iteration number (default: 1)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output HTML file path (auto-generated if not specified)")
    parser.add_argument("--open", action="store_true", help="Open the plot in a web browser")

    args = parser.parse_args()

    # Load JSON
    if not os.path.exists(args.results_json):
        print(f"Error: Results JSON file not found: {args.results_json}")
        sys.exit(1)

    results_dict = load_results_json(args.results_json)
    iteration_str = str(args.iteration)

    # Discover available variables
    iter_vars = get_time_stepped_variables(results_dict, iteration_str)
    prob_vars = get_probabilistic_variables(results_dict)

    all_vars = {}
    all_vars.update({k: ("iteration", v) for k, v in iter_vars.items()})
    all_vars.update({k: ("probabilistic", v) for k, v in prob_vars.items()})

    # If no variables requested, list available ones
    if not args.variables:
        print(f"\nAvailable time-stepped variables (iteration {args.iteration}):")
        print("-" * 50)
        if iter_vars:
            for var_name in sorted(iter_vars.keys()):
                num_steps = len(iter_vars[var_name])
                print(f"  {var_name}  ({num_steps} time steps)")
        if prob_vars:
            print(f"\nAvailable probabilistic variables:")
            print("-" * 50)
            for var_name in sorted(prob_vars.keys()):
                num_steps = len(prob_vars[var_name])
                print(f"  {var_name}  ({num_steps} time steps)")

        # Show grid bounds
        iter_data = results_dict["iterations"].get(iteration_str, {})
        if iter_data:
            print(f"\nGrid bounds:")
            print(f"  X: {iter_data.get('gridUniqueX_min', '?')} to {iter_data.get('gridUniqueX_max', '?')} (dX={iter_data.get('deltaX', '?')})")
            print(f"  Y: {iter_data.get('gridUniqueY_min', '?')} to {iter_data.get('gridUniqueY_max', '?')} (dY={iter_data.get('deltaY', '?')})")
        return

    # Validate requested variables
    requested_vars = []
    for var_name in args.variables:
        if var_name in all_vars:
            requested_vars.append(var_name)
        else:
            print(f"Warning: Variable '{var_name}' not found. Available: {', '.join(sorted(all_vars.keys()))}")

    if not requested_vars:
        print("Error: No valid variables specified.")
        sys.exit(1)

    # Compute time values
    time_values, time_unit_label, dt_seconds, convert_time = compute_time_values(results_dict)

    # Extract time series for each variable
    plot_data = []
    final_matched_x = args.x
    final_matched_y = args.y

    for var_name in requested_vars:
        source_type, var_file_dict = all_vars[var_name]
        print(f"Extracting '{var_name}' at ({args.x}, {args.y})...")

        time_indices, values, matched_x, matched_y = extract_time_series(var_file_dict, args.x, args.y)

        if len(values) == 0:
            print(f"  Warning: No data found for '{var_name}'. Skipping.")
            continue

        if matched_x is not None:
            final_matched_x = matched_x
            final_matched_y = matched_y

        print(f"  Matched grid point: ({matched_x}, {matched_y}), {len(values)} time steps")
        plot_data.append((var_name, time_indices, values))

    if not plot_data:
        print("Error: No data to plot.")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        results_dir = os.path.dirname(args.results_json)
        var_names_str = "_".join(requested_vars[:3])
        if len(requested_vars) > 3:
            var_names_str += f"_+{len(requested_vars)-3}more"
        output_path = os.path.join(
            results_dir,
            f"time_graph_x{args.x}_y{args.y}_{var_names_str}.html"
        )

    # Generate plot
    plot_time_graph(
        plot_data, time_values, time_unit_label,
        args.x, args.y, final_matched_x, final_matched_y,
        output_path, open_html=args.open
    )


if __name__ == '__main__':
    main()
