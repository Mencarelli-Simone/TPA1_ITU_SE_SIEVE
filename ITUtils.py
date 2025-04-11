import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from pandarallel import pandarallel

def itu_to_bandwidth(itu_designation):
    """
    Convert ITU designation of emission to bandwidth in Hz.
    Parameters:
    itu_designation (str): ITU designation of emission (e.g., "6K00A3E")
    Returns:
    float: Bandwidth in Hz
    """
    # Check for NaN values
    if pd.isna(itu_designation):
        return np.nan
    # Ensure itu_designation is a string
    itu_designation = str(itu_designation)
    # Extract the bandwidth part of the ITU designation
    bandwidth_str = itu_designation[:4]
    # Determine the multiplier based on the last character
    multiplier = {
        'H': 1,
        'K': 1e3,
        'M': 1e6,
        'G': 1e9
    }
    multipliers = ['H', 'K', 'M', 'G']
    for m in multipliers:
        index = bandwidth_str.find(m)
        if index != -1:
            multi = bandwidth_str[index]
            break
        else:
            index = 3
    integer = bandwidth_str[:index]
    if index < 3:
        decimal = bandwidth_str[index + 1:]
    else:
        decimal = '0'
    if len(decimal) == 0:
        decimal = '0'
    if len(integer) == 0:
        decimal = '0'
    bandwidth = 0.0 + (float(int(integer)) + int(decimal) * 10 ** (-len(decimal))) * multiplier[multi]
    return bandwidth


def channel_appender(df: pd.DataFrame) -> pd.DataFrame:
    """
    :param df: has to be a dataframe containing an ITU space explorer database
    :return: a copy of the dataframe with extra columns for channel bandwidth, channel fmin and fmax
    """
    # Add columns for channel bandwidth, channel frequency minimum, and channel frequency maximum
    df.loc[:, ' channel.bandwidth'] = df[' emiss.design_emi'].apply(
        lambda x: itu_to_bandwidth(x))  # Convert to MHz
    df.loc[:, ' channel.freq_min'] = df[' carrier_fr.freq_carr'] - (df[' channel.bandwidth'] / 1e6 / 2)
    df.loc[:, ' channel.freq_max'] = df[' carrier_fr.freq_carr'] + (df[' channel.bandwidth'] / 1e6 / 2)
    return df


def conflicts_appender(targetdf: pd.DataFrame, referencedf: pd.DataFrame) -> pd.DataFrame:
    """
    :param targetdf: has to be a dataframe containing an ITU space explorer database
    :param referencedf: dataframe containing the TPA dataframe
    :return: columns appended with conflicts, and subset_with_nans
    """
    # Initialize pandarallel
    num_logical_processors = os.cpu_count()
    pandarallel.initialize(nb_workers=num_logical_processors, progress_bar=True)

    ddf = channel_appender(targetdf)

    # Ensure the tpaconflicts and percentoverlap columns exist in ddf
    if 'tpaconflicts' not in ddf.columns:
        ddf['tpaconflicts'] = ''
    if 'percentoverlap' not in ddf.columns:
        ddf['percentoverlap'] = ''

    # Create a subset of the DataFrame with NaN values in the specified columns
    subset_with_nan = ddf[ddf[[' channel.freq_max', ' channel.freq_min']].isna().any(axis=1)]

    # Remove rows with NaN values in 'channel.freq_max' or 'channel.freq_min'
    ddf = ddf.dropna(subset=[ ' channel.freq_max', ' channel.freq_min'])

    # Define a function to check for overlaps and update the tpaconflicts and percentoverlap columns
    def check_overlap(ddf_row, tpa):
        conflicts = ''
        percent_overlap_list = []
        for tpa_index, tpa_row in tpa.iterrows():
            tpa_fmax = tpa_row[' channel.freq_max']
            tpa_fmin = tpa_row[' channel.freq_min']
            ddf_fmax = ddf_row[' channel.freq_max']
            ddf_fmin = ddf_row[' channel.freq_min']

            # Check if intervals overlap
            if not (tpa_fmax < ddf_fmin or tpa_fmin > ddf_fmax):
                conflicts += f"{tpa_index}:"
                overlap_start = max(tpa_fmin, ddf_fmin)
                overlap_end = min(tpa_fmax, ddf_fmax)
                overlap_length = overlap_end - overlap_start
                tpa_length = tpa_fmax - tpa_fmin
                percent_overlap = (overlap_length / tpa_length) * 100
                percent_overlap_list.append(f"{percent_overlap:.0f}")

        percent_overlap_str = ":".join(percent_overlap_list)
        return conflicts, percent_overlap_str

    # Apply the function to each row of the ddf DataFrame in parallel
    ddf[['tpaconflicts', 'percentoverlap']] = ddf.parallel_apply(
        lambda row: check_overlap(row, referencedf), axis=1, result_type='expand'
    )

    # Filter out non-conflicting rows
    ddf_conflicts = ddf[ddf['tpaconflicts'] != '']

    return ddf_conflicts, subset_with_nan

def conflict_expander(ddf_conflicts: pd.DataFrame, referencedf: pd.DataFrame) -> pd.DataFrame:
    """
    explicits the type of conflict and appends a string containing percent,case under a colum corresponding to the
    conflicted tpa channel
    :param ddf_conflicts:
    :param referencedf:
    :return:
    """
    # step 1, for every TPA emission add a column with title TPA1.fmin-fmax_E or TPA1.fmin-fmax_R
    emissionnames = []

    for tpa_index, tpa_row in referencedf.iterrows():
        tpa_fmax = tpa_row['channel.freq_max']
        tpa_fmin = tpa_row['channel.freq_min']
        emistype = tpa_row[' s_beam.emi_rcp']
        name = str('TPA1.'+tpa_fmin+'-'+tpa_fmax+'_'+emistype)
        emissionnames.append(name)
    print(emissionnames)