import pandas as pd
import numpy as np

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
