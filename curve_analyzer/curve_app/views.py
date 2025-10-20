from django.shortcuts import render 
from django.http import JsonResponse
import pandas as pd
import io
import numpy as np
import scipy.interpolate as interp
import scipy.signal
import re
from typing import List, Tuple, Any

w = 5e-6  # channel_width

def index(request):
    return render(request, 'index.html')

def analyze_data(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'})

    if 'data' not in request.FILES:
        return JsonResponse({'error': 'File non ricevuto'})

    file = request.FILES['data']
    x_column = (request.POST.get('x_column', '') or '').strip()
    y_column = (request.POST.get('y_column', '') or '').strip()
    color_column = (request.POST.get('color_column', '') or '').strip()
    # color strategy: continuous, kmeans, categorical, auto
    color_method = (request.POST.get('color_method', '') or 'auto').strip().lower()
    try:
        color_k = int(request.POST.get('color_k', 5))
    except Exception:
        color_k = 5
    print(color_column)
    print(x_column)
    # --- Read the file into a DataFrame
    data_str = b''.join(file.readlines()).decode('utf-8', errors='replace')
    data = io.StringIO(data_str)
    try:
        df = pd.read_csv(data, sep='\t')
        # keep a raw string copy for columns that must preserve categories (e.g., color column)
        raw_df = pd.read_csv(io.StringIO(data_str), sep='\t', dtype=str)
    except Exception as e:
        return JsonResponse({'error': f'Errore lettura file: {str(e)}'})

    # Normalize column names to be robust to leading/trailing and non-standard whitespace
    def _normalize_col_name(c):
        # replace non-breaking spaces, collapse whitespace and strip
        if c is None:
            return c
        s = str(c).replace('\xa0', ' ')
        s = re.sub(r"\s+", ' ', s)
        return s.strip()

    df.columns = [_normalize_col_name(c) for c in df.columns]
    
    raw_df.columns = [_normalize_col_name(c) for c in raw_df.columns]


    # prepare raw column value arrays for positional selection (preserve categories)
    raw_values_by_col = {col: raw_df[col].astype(str).values for col in raw_df.columns}

    # Validate selected columns
    if x_column not in df.columns or y_column not in df.columns:
        return JsonResponse({
            'error': f"Colonna non trovata: '{x_column}' o '{y_column}'. Colonne disponibili: {', '.join(df.columns)}"
        })

    # If user provided a color column name, try a case-insensitive match to the normalized headers
    if color_column and color_column not in df.columns:
        # try case-insensitive exact match
        ci_matches = [c for c in df.columns if c.lower() == color_column.lower()]
        if ci_matches:
            color_column = ci_matches[0]
    
    # Clean up data types
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Check for required grouping column
    if 'VDS' not in df.columns:
        return JsonResponse({
            'error': "Colonna 'VDS' mancante dal file. Colonne disponibili: " + ', '.join(df.columns)
        })

    vds_list = np.unique(df['VDS'].dropna().values)
    result_data = {
        'x_values': [],
        'y_values': []
    }
    color_values_out = []
    legend_out = []
    warnings = []

    max_points_per_sweep = 200  # <= Change as needed

    for z in vds_list:
        # select rows for this VDS group from numeric df
        sel_df = (df['VDS'] == z)
        x_all = df.loc[sel_df, x_column].values
        y_all = df.loc[sel_df, y_column].values

        # select raw color column values for the same rows as numeric df (preserve categories)
        color_col_all = None
        if color_column and color_column in raw_values_by_col:
            try:
                sel_positions = np.where(sel_df)[0]
                color_col_all = raw_values_by_col[color_column][sel_positions]
            except Exception:
                color_col_all = None

        # Remove NaN and ensure there are at least two unique x points
        mask_valid = (~np.isnan(x_all)) & (~np.isnan(y_all))
        x = x_all[mask_valid]
        y = y_all[mask_valid]
        # align color column values to the numeric rows (if available)
        if color_col_all is not None and len(color_col_all) == len(x_all):
            try:
                color_col_vals = color_col_all[mask_valid]
            except Exception:
                color_col_vals = None
        else:
            color_col_vals = None
        if len(np.unique(x)) < 2:
            warnings.append(f"VDS={z}: dati insufficienti ({len(x)} punti validi)")
            continue

        dx = np.diff(x)
        dy = np.diff(y)
        with np.errstate(divide='ignore', invalid='ignore'):
            derivative = np.where(dx != 0, dy / (dx * w), np.nan)
        mask = ~np.isnan(derivative) & np.isfinite(derivative)
        x_clean = x[:-1][mask]
        derivative_clean = derivative[mask]
        if len(x_clean) < 2:
            warnings.append(f"VDS={z}: dati insufficienti per interpolazione dopo il filtraggio")
            continue

        # Remove duplicates
        x_clean, unique_indices = np.unique(x_clean, return_index=True)
        derivative_clean = derivative_clean[unique_indices]
        if len(x_clean) < 2:
            warnings.append(f"VDS={z}: valori x duplicati, nessuna interpolazione possibile")
            continue

        try:
            f = interp.interp1d(x_clean, derivative_clean, fill_value="extrapolate", kind='slinear')
            xx_0 = np.linspace(min(x_clean), max(x_clean), 5000)
            yy_0 = f(xx_0)
            valid_mask = np.isfinite(yy_0)
            xx_1 = xx_0[valid_mask]
            yy_1 = yy_0[valid_mask]
            window = scipy.signal.windows.gaussian(200, 60)
            yy_smooth = scipy.signal.convolve(yy_1, window / window.sum(), mode='same')

            # prepare color source aligned with derivative points (x[:-1])
            if color_col_vals is not None:
                try:
                    color_src = color_col_vals[:-1][mask]
                    # align color_src with the unique x_clean indices used for interpolation
                    # unique_indices was computed above when deduplicating x_clean
                    if 'unique_indices' in locals() and color_src is not None:
                        try:
                            # ensure indices are within range
                            if np.max(unique_indices) < len(color_src):
                                color_src = color_src[unique_indices]
                            else:
                                color_src = None
                        except Exception:
                            color_src = None
                except Exception:
                    color_src = None
            else:
                color_src = None

            # ---- DOWNSAMPLE BEFORE SENDING TO FRONTEND! ----
            if len(xx_1) > max_points_per_sweep:
                idx = np.round(np.linspace(0, len(xx_1) - 1, max_points_per_sweep)).astype(int)
                xx_1_down = xx_1[idx]
                yy_smooth_down = yy_smooth[idx]
                # map color_src to downsampled points using nearest neighbor
                if color_src is not None and len(color_src) == len(x_clean):
                    chosen = []
                    for xi in xx_1_down:
                        # find nearest x_clean value
                        nearest = np.argmin(np.abs(x_clean - xi))
                        chosen.append(color_src[nearest])
                    color_down = np.array(chosen)
                else:
                    color_down = None
            else:
                xx_1_down = xx_1
                yy_smooth_down = yy_smooth
                if color_src is not None and len(color_src) == len(x_clean):
                    # map each xx_1 point to nearest x_clean
                    chosen = []
                    for xi in xx_1_down:
                        nearest = np.argmin(np.abs(x_clean - xi))
                        chosen.append(color_src[nearest])
                    color_down = np.array(chosen)
                else:
                    color_down = None

            result_data['x_values'].extend(xx_1_down.tolist())
            result_data['y_values'].extend(yy_smooth_down.tolist())
            # collect per-group downsampled color arrays for global mapping later
            if color_column and (color_down is not None):
                # store the downsampled color values for this group
                if 'color_group_downs' not in locals():
                    color_group_downs = []
                    group_point_counts = []
                color_group_downs.append(np.array(color_down, dtype=object))
                group_point_counts.append(len(xx_1_down))
            else:
                # mark this group as having no color data
                if 'color_group_downs' not in locals():
                    color_group_downs = []
                    group_point_counts = []
                color_group_downs.append(None)
                group_point_counts.append(len(xx_1_down))

        except Exception as ex:
            warnings.append(f"Errore durante l'interpolazione per VDS={z}: {str(ex)}")

    # Always return at least an empty result (not error), plus warnings if any
    # post-process color_values_out: if all None, return no color_values
    # If a color column was provided, perform a global mapping across all downsampled group values
    if color_column:
        try:
            # if we collected per-group downs, concatenate them in order, skipping None groups
            all_down = []
            group_indices = []  # tuple(start, end) for each group
            pos = 0
            for g in (color_group_downs if 'color_group_downs' in locals() else []):
                if g is None:
                    group_indices.append((None, None))
                else:
                    start = pos
                    end = pos + len(g)
                    group_indices.append((start, end))
                    all_down.extend(g.tolist())
                    pos = end

            if len(all_down) > 0:
                mapped_all, legend = map_values_and_legend(np.array(all_down, dtype=object), method='quantile', k=color_k)
                # split mapped_all back into per-group color lists and extend color_values_out in order
                color_values_out = []
                offset = 0
                total_expected = sum(group_point_counts) if 'group_point_counts' in locals() else 0
                # If mapped_all length mismatches expected, clamp to available length
                mapped_len = len(mapped_all) if mapped_all is not None else 0
                for i, g in enumerate((color_group_downs if 'color_group_downs' in locals() else [])):
                    pts = group_point_counts[i] if ('group_point_counts' in locals() and i < len(group_point_counts)) else 0
                    if g is None or pts == 0:
                        # fill with None placeholders for groups without color data
                        color_values_out.extend([None] * pts)
                    else:
                        # slice mapped_all for this group's points
                        seg = mapped_all[offset: offset + pts]
                        # if seg shorter than pts, pad with None
                        if len(seg) < pts:
                            seg = list(seg) + [None] * (pts - len(seg))
                        color_values_out.extend(seg)
                        offset += pts
                # set legend if present
                legend_out = legend or []
            else:
                color_values_out = None
        except Exception:
            # on any error, set to None to avoid breaking the client
            color_values_out = None
    else:
        if len(color_values_out) == 0 or all([cv is None for cv in color_values_out]):
            color_values_out = None

    # Debug information to help compare lengths and sample items in the browser
    debug = {
        'result_x_len': len(result_data.get('x_values', [])),
        'result_y_len': len(result_data.get('y_values', [])),
        'color_values_len': len(color_values_out) if color_values_out is not None else None,
        'result_x_sample': result_data.get('x_values', [])[:8],
        'color_values_sample': (color_values_out[:8] if color_values_out is not None else None),
    }
    # include legend in debug for now
    debug['legend'] = legend_out or None

    # per-group debug (lengths) to help trace mismatches between numeric rows and raw color rows
    # This is intentionally lightweight; remove in production
    group_debug = []
    for z in vds_list:
        try:
            sel_df_idx = df.index[df['VDS'] == z]
            x_len = len(df.loc[sel_df_idx, x_column].values)
            try:
                raw_len = len(raw_df.loc[sel_df_idx, color_column].values) if color_column else None
            except Exception:
                raw_len = None
            group_debug.append({'VDS': str(z), 'x_rows': x_len, 'raw_color_rows': raw_len})
        except Exception:
            group_debug.append({'VDS': str(z), 'x_rows': None, 'raw_color_rows': None})
    debug['groups'] = group_debug

    return JsonResponse({'result': result_data, 'warnings': warnings, 'color_values': color_values_out, 'legend': legend_out or None, 'debug': debug})


def map_values_to_colors(values):
    """Map numeric or categorical array to CSS rgba strings.
    - numeric: normalize and map to a simple HSL-based colormap
    - categorical: map unique categories to distinct hues
    Returns list of strings like 'rgba(r,g,b,a)'.
    """
    # convert to numpy array
    arr = np.array(values)
    # try numeric
    try:
        nums = arr.astype(float)
        # handle NaN
        mask = np.isfinite(nums)
        out = [None] * len(nums)
        if mask.any():
            mn = np.nanmin(nums)
            mx = np.nanmax(nums)
            span = mx - mn if mx != mn else 1.0
            for i, v in enumerate(nums):
                if not np.isfinite(v):
                    out[i] = 'rgba(200,200,200,0.6)'
                else:
                    # normalize 0..1
                    t = (v - mn) / span
                    # map to hue 240 (blue) -> 0 (red)
                    hue = (1.0 - t) * 240
                    r, g, b = hsl_to_rgb(hue / 360.0, 0.7, 0.5)
                    out[i] = f'rgba({int(r)},{int(g)},{int(b)},0.9)'
        return out
    except Exception:
        # categorical path
        uniques, inverse = np.unique(arr.astype(str), return_inverse=True)
        hues = np.linspace(0, 360, num=len(uniques), endpoint=False)
        out = []
        for idx in inverse:
            h = hues[idx]
            r, g, b = hsl_to_rgb(h / 360.0, 0.7, 0.5)
            out.append(f'rgba({int(r)},{int(g)},{int(b)},0.9)')
        return out


def simple_kmeans(vals: np.ndarray, k: int, iters: int = 20) -> Tuple[np.ndarray, np.ndarray]:
    """A tiny 1-D k-means to avoid external deps. Returns labels and centers."""
    # convert to float, handle NaN by placing into a special bucket (-inf)
    arr = np.array(vals, dtype=float)
    mask = np.isfinite(arr)
    if mask.sum() == 0:
        return np.array([]), np.array([])
    data = arr[mask]
    mn, mx = data.min(), data.max()
    if mn == mx:
        centers = np.array([mn])
        labels = np.zeros(len(arr), dtype=int)
        return labels, centers
    # initialize centers evenly
    centers = np.linspace(mn, mx, num=k)
    labels_full = np.zeros(len(arr), dtype=int)
    for _ in range(iters):
        # assign
        dists = np.abs(data[:, None] - centers[None, :])
        lbl = dists.argmin(axis=1)
        # recompute centers
        new_centers = np.array([data[lbl == i].mean() if (lbl == i).any() else centers[i] for i in range(len(centers))])
        if np.allclose(new_centers, centers):
            break
        centers = new_centers
    # expand labels to original length (put NaNs to -1 bucket)
    full_labels = np.full(len(arr), -1, dtype=int)
    full_labels[mask] = lbl
    return full_labels, centers


def map_values_and_legend(values: np.ndarray, method: str = 'auto', k: int = 5) -> Tuple[List[str], List[dict]]:
    """Map an array of values (strings or numbers) to color strings and produce a legend list.
    Legend items: {label: str, color: 'rgba(...)'}
    Returns (mapped_colors_list, legend_list)
    """
    arr = np.array(values)

    # Try to interpret as numeric values
    is_numeric = False
    try:
        nums = arr.astype(float)
        is_numeric = True
    except Exception:
        nums = None

    # If auto, treat numeric as quantile-binned categorical, otherwise categorical
    if method == 'auto':
        method = 'quantile' if is_numeric else 'categorical'

    # Numeric -> quantile binning into k buckets (simple and robust)
    if method in ('quantile', 'numeric') and is_numeric:
        # mask finite values
        mask = np.isfinite(nums)
        mapped = [None] * len(nums)
        legend = []
        if mask.sum() == 0:
            # nothing numeric
            return [None] * len(nums), []

        s = pd.Series(nums[mask])
        # If there are fewer distinct values than k, fall back to unique-value categorical mapping
        if s.nunique() <= max(1, int(k)):
            uniques = np.sort(s.unique())
            hues = np.linspace(0, 360, num=len(uniques), endpoint=False)
            val_to_color = {}
            for i, u in enumerate(uniques):
                r, g, b = hsl_to_rgb(hues[i] / 360.0, 0.7, 0.5)
                val_to_color[u] = f'rgba({int(r)},{int(g)},{int(b)},0.9)'
                legend.append({'label': f'{u:.3g}', 'color': val_to_color[u]})
            # assign
            for idx, v in enumerate(nums):
                if not np.isfinite(v):
                    mapped[idx] = 'rgba(200,200,200,0.6)'
                else:
                    mapped[idx] = val_to_color.get(v, 'rgba(150,150,150,0.9)')
            return mapped, legend

        # Use qcut to produce roughly equal-sized bins; drop duplicates if needed
        try:
            cats, bins = pd.qcut(s, q=int(k), retbins=True, labels=False, duplicates='drop')
        except Exception:
            # fallback to equal-width bins
            cats, bins = pd.cut(s, bins=int(k), retbins=True, labels=False, duplicates='drop')

        # Build colors for each bin
        unique_bins = np.unique(cats)
        hues = np.linspace(0, 360, num=len(unique_bins), endpoint=False)
        bin_to_color = {}
        for i, bidx in enumerate(unique_bins):
            r, g, b = hsl_to_rgb(hues[i] / 360.0, 0.7, 0.5)
            bin_to_color[int(bidx)] = f'rgba({int(r)},{int(g)},{int(b)},0.9)'

        # Build legend using bin edges
        # bins are the edges returned from qcut/cut on the finite subset; construct readable labels
        if len(bins) >= 2:
            # bins is array of edges, length = n_bins+1
            for i in range(len(bins) - 1):
                lo = bins[i]
                hi = bins[i + 1]
                # find a color for this bin if present
                color = bin_to_color.get(i, 'rgba(150,150,150,0.9)')
                legend.append({'label': f'{lo:.3g}–{hi:.3g}', 'color': color})
        else:
            # single bin
            legend.append({'label': f'{s.min():.3g}–{s.max():.3g}', 'color': bin_to_color.get(0, 'rgba(150,150,150,0.9)')})

        # assign mapped colors back to original positions
        # cats corresponds to s (the masked finite values)
        mapped = []
        m_iter = iter(cats.tolist())
        for i in range(len(nums)):
            if not mask[i]:
                mapped.append('rgba(200,200,200,0.6)')
            else:
                bidx = next(m_iter)
                mapped.append(bin_to_color.get(int(bidx), 'rgba(150,150,150,0.9)'))

        return mapped, legend

    # Categorical mapping for string/non-numeric values
    # Convert to string to group reliably
    str_arr = arr.astype(str)
    uniques, inverse = np.unique(str_arr, return_inverse=True)
    hues = np.linspace(0, 360, num=len(uniques) if len(uniques) > 0 else 1, endpoint=False)
    legend = []
    val_to_color = {}
    for i, u in enumerate(uniques):
        r, g, b = hsl_to_rgb(hues[i] / 360.0, 0.7, 0.5)
        color = f'rgba({int(r)},{int(g)},{int(b)},0.9)'
        legend.append({'label': str(u), 'color': color})
        val_to_color[u] = color
    mapped = [val_to_color.get(v, 'rgba(150,150,150,0.9)') for v in str_arr]
    return mapped, legend


def hsl_to_rgb(h, s, l):
    """Convert HSL (h in 0..1) to RGB 0..255. Simple implementation."""
    if s == 0:
        r = g = b = int(l * 255)
        return r, g, b
    def hue2rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p
    q = l + s - l * s if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
    return int(r * 255), int(g * 255), int(b * 255)
