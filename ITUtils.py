import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from pandarallel import pandarallel
from time import sleep


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

    ddf = channel_appender(targetdf)  # ok

    # Ensure the tpaconflicts and percentoverlap columns exist in ddf
    if 'tpaconflicts' not in ddf.columns:
        ddf['tpaconflicts'] = ''
    if 'percentoverlap' not in ddf.columns:
        ddf['percentoverlap'] = ''

    # Create a subset of the DataFrame with NaN values in the specified columns
    subset_with_nan = ddf[ddf[[' channel.freq_max', ' channel.freq_min']].isna().any(axis=1)]

    # Remove rows with NaN values in 'channel.freq_max' or 'channel.freq_min'
    ddf = ddf.dropna(subset=[' channel.freq_max', ' channel.freq_min'])

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
            if not (tpa_fmax <= ddf_fmin or tpa_fmin >= ddf_fmax):
                conflicts += f"{tpa_index}:"
                overlap_start = max(tpa_fmin, ddf_fmin)
                overlap_end = min(tpa_fmax, ddf_fmax)
                overlap_length = overlap_end - overlap_start
                ddf_length = ddf_fmax - ddf_fmin
                tpa_length = tpa_fmax - tpa_fmin
                percent_overlap = (overlap_length / ddf_length) * 100
                percent_overlap_list.append(f"{percent_overlap:.0f}")

        percent_overlap_str = ":".join(percent_overlap_list)
        return conflicts, percent_overlap_str

    # Apply the function to each row of the ddf DataFrame in parallel
    # ddf[['tpaconflicts', 'percentoverlap']] = ddf.parallel_apply(
    #     lambda row: check_overlap(row, referencedf), axis=1, result_type='expand'
    # )

    ddf[['tpaconflicts', 'percentoverlap']] = ddf.parallel_apply(
        lambda row: check_overlap(row, referencedf), axis=1, result_type='expand'
    )

    # Filter out non-conflicting rows
    ddf_conflicts = ddf[ddf['tpaconflicts'] != '']

    return ddf_conflicts, subset_with_nan


def conflict_expander(ddf_conflicts: pd.DataFrame, referencedf: pd.DataFrame, eminames=False) -> pd.DataFrame:
    """
    explicits the type of conflict and appends a string containing percent,case under a colum corresponding to the
    conflicted tpa channel
    :param ddf_conflicts: table to expand
    :param referencedf: referende dataframe
    :return:
    """
    # # Initialize pandarallel
    # num_logical_processors = os.cpu_count()
    # pandarallel.initialize(nb_workers=num_logical_processors, progress_bar=True)
    # step 1, for every TPA emission add a column with title TPA1.fmin-fmax_E or TPA1.fmin-fmax_R
    emissionnames = []

    for tpa_index, tpa_row in referencedf.iterrows():
        tpa_fmax = tpa_row[' channel.freq_max']
        tpa_fmin = tpa_row[' channel.freq_min']
        emistype = tpa_row[' s_beam.emi_rcp']
        name = str('TPA1.' + str(tpa_fmin) + '-' + str(tpa_fmax) + '_' + emistype)
        emissionnames.append(name)
    print(emissionnames)
    # emissionnames is a lookup for the index
    # the goal now is to append all the emissionnames as columns and fill each column with the corresponding percentual
    # and conflict type e.g ER97
    # CONFLICT TYPES first letter TPA emission type (last letter of the column title)
    #                second letter Other emission type (current row ' s_beam.emi_rcp')
    # (A) ER = TPA emitting Other receiving
    # (B) EE = TPA emitting Other emitting (Other BS receiving)
    # (C) RR = TPA receiving Other receiving
    # (D) RE = TPA receiving Other emitting (this is not a problem for others)
    # append columns to ddf_conflicts
    for name in emissionnames:
        ddf_conflicts[name] = None

    def conflict_distributor(df_row):
        conflicts_string = str(df_row['tpaconflicts'])
        percent_string = str(df_row['percentoverlap'])
        conflicts_str = conflicts_string.split(":")  # this is effectively an index
        conflicts = []
        for c in conflicts_str:
            if c not in [None, '', 'nan'] and not pd.isna(c) and not pd.isna(int(c)):
                conflicts.append(int(c))
        # print(conflicts)
        percent = percent_string.split(":")
        conflicts = conflicts[0:len(percent)]  # ensure there is no empty conflict at the end
        # find the conflict type for every conflict
        types = []
        for conf, perc in zip(conflicts, percent):
            tpa_emistype = emissionnames[conf][-1]
            other_emistype = df_row[' s_beam.emi_rcp'].strip()
            if tpa_emistype == 'E' and other_emistype == 'R':
                conflict_type = 'ER'
            elif tpa_emistype == 'E' and other_emistype == 'E':
                conflict_type = 'EE'
            elif tpa_emistype == 'R' and other_emistype == 'R':
                conflict_type = 'RR'
            elif tpa_emistype == 'R' and other_emistype == 'E':
                conflict_type = 'RE'
            else:
                conflict_type = 'NA'
            types.append(f"{int(perc):>3}%{conflict_type}")
        # fill the columns
        for conf, type in zip(conflicts, types):
            df_row[emissionnames[conf]] = type
        return df_row

    # apply to whole table using pandarallel as other function
    if len(ddf_conflicts) > 24:
        ddf_conflicts = ddf_conflicts.parallel_apply(conflict_distributor, axis=1)
    else:
        ddf_conflicts = ddf_conflicts.apply(conflict_distributor, axis=1)  # for debugging
    if eminames:
        return ddf_conflicts, emissionnames
    else:
        return ddf_conflicts


def sat_names_isolator(df: pd.DataFrame, namesfolder: str) -> pd.DataFrame:
    """
    separates the entries with satellite names contained in the names folder
    outputs two dataframes, one with all the listed satellite names and the other with the remaining entries
    : param df: dataframe containing satellite names
    : param namesfolder: folder containing satellite names
    : return: matched_df, discarded_df
    """
    # Initialize an empty list to store the data
    big_list = []

    # Iterate over each file in the folder
    for filename in os.listdir(namesfolder):
        if filename.endswith('.txt'):
            # Construct the full file path
            file_path = os.path.join(namesfolder, filename)

            # Open and read the file
            with open(file_path, 'r') as file:
                # Read the content and split by commas
                content = file.read().strip().split(', ')
                # Extend the big list with the content
                big_list.extend(content)

    # Isolate the lines where the name corresponds to one of the big list entries
    matched_df = df[df[' com_el.sat_name'].isin(big_list)]

    # Create the discarded dataframe with the remaining lines
    discarded_df = df[~df[' com_el.sat_name'].isin(big_list)]

    return matched_df, discarded_df, big_list


def conflict_tables_separator(expanded: pd.DataFrame, referencedf: pd.DataFrame, outfolder) -> pd.DataFrame:
    """
    explicits the type of conflict and appends a string containing percent,case under a colum corresponding to the
    conflicted tpa channel
    :param expanded: table to expand
    :param referencedf: referende dataframe
    :param outfolder: folder path for output tables
    :return:
    """
    # Initialize pandarallel
    num_logical_processors = os.cpu_count()
    pandarallel.initialize(nb_workers=num_logical_processors, progress_bar=True)
    # step 1, for every TPA emission add a column with title TPA1.fmin-fmax_E or TPA1.fmin-fmax_R
    emissionnames = []
    for tpa_index, tpa_row in referencedf.iterrows():
        tpa_fmax = tpa_row[' channel.freq_max']
        tpa_fmin = tpa_row[' channel.freq_min']
        emistype = tpa_row[' s_beam.emi_rcp']
        name = str('TPA1.' + str(tpa_fmin) + '-' + str(tpa_fmax) + '_' + emistype)
        emissionnames.append(name)
    print(emissionnames)

    for name in emissionnames:
        # Only keep rows where the column 'name' is not None
        subset_df = expanded[expanded[name].notna()]

        # Separate entries with 'E' and entries with 'R'
        subset_E = subset_df[subset_df[' s_beam.emi_rcp'].str.contains('E', na=False)]
        subset_R = subset_df[subset_df[' s_beam.emi_rcp'].str.contains('R', na=False)]

        # Separate entries where 's_beam.emi_rcp' is NaN
        subset_N = subset_df[~subset_df.index.isin(subset_E.index) & ~subset_df.index.isin(subset_R.index)]

        # Sort each subset by the 'name' column in descending order
        subset_E = subset_E.sort_values(by=name, ascending=False)
        subset_R = subset_R.sort_values(by=name, ascending=False)
        subset_N = subset_N.sort_values(by=name, ascending=False)

        # Save the subsets to the specified folder if they are not empty
        if not subset_E.empty:
            subset_E.to_csv(os.path.join(outfolder, f"{name}_E.csv"), index=False)
            print('table saved to', os.path.join(outfolder, f"{name}_E.csv"))
        if not subset_R.empty:
            subset_R.to_csv(os.path.join(outfolder, f"{name}_R.csv"), index=False)
            print('table saved to', os.path.join(outfolder, f"{name}_R.csv"))
        if not subset_N.empty:
            subset_N.to_csv(os.path.join(outfolder, f"{name}_N.csv"), index=False)
            print('table saved to', os.path.join(outfolder, f"{name}_N.csv"))

        # Create subsets with only one entry per unique 'com_el.sat_name'
        unique_subset_E = subset_E.drop_duplicates(subset=' com_el.sat_name', keep='first')
        unique_subset_R = subset_R.drop_duplicates(subset=' com_el.sat_name', keep='first')
        unique_subset_N = subset_N.drop_duplicates(subset=' com_el.sat_name', keep='first')

        # Save the unique subsets to the specified folder if they are not empty
        if not unique_subset_E.empty:
            unique_subset_E.to_csv(os.path.join(outfolder, f"{name}_E_worstcase.csv"), index=False)
            print('table saved to', os.path.join(outfolder, f"{name}_E_worstcase.csv"))
        if not unique_subset_R.empty:
            unique_subset_R.to_csv(os.path.join(outfolder, f"{name}_R_worstcase.csv"), index=False)
            print('table saved to', os.path.join(outfolder, f"{name}_R_worstcase.csv"))
        if not unique_subset_N.empty:
            unique_subset_N.to_csv(os.path.join(outfolder, f"{name}_N_worstcase.csv"), index=False)
            print('table saved to', os.path.join(outfolder, f"{name}_N_worstcase.csv"))


def country_conflicts_finder(countrycode: str, referencedf: pd.DataFrame, tablesfolder: str, namesfolder: str,
                             outfolder: str, disp=True) -> pd.DataFrame:
    """
    :param countrycode: adm country code
    :param referencedf: tpa mission df
    :param tablesfolder: folder with adm tables
    :param namesfolder: folder with adm satellite names lists
    :return expanded_table, expanded_rejected, expanded_simplified, noinfofoundmissions
    """

    # Initialize pandarallel
    num_logical_processors = os.cpu_count()
    pandarallel.initialize(nb_workers=num_logical_processors, progress_bar=True)

    # load in a single dataframe all tables corresponding to the country code
    all_tables = []
    for filename in os.listdir(tablesfolder):
        if str(countrycode) in filename[:len(countrycode)]:
            print('loading ', filename)
            filepath = os.path.join(tablesfolder, filename)
            df = pd.read_csv(filepath, low_memory=False)
            all_tables.append(df)
    combined_df = pd.concat(all_tables, ignore_index=True)
    # drop all entries with different countrycode
    combined_df = combined_df[combined_df[' com_el.adm'] == countrycode]

    # now apply the conflict detection to the combined_df
    print('finding conflicts for ', countrycode)
    conflicts, noinfo = conflicts_appender(combined_df, referencedf)
    # save conflicts
    os.makedirs(os.path.join(outfolder, 'output_tables'), exist_ok=True)

    conflicts.to_csv(os.path.join(outfolder, 'conflicts.csv'), index=False)
    print('file saved to ', os.path.join(outfolder, 'conflicts.csv'))
    # get the reference names
    namelist = []
    # Iterate over each file in the folder
    for filename in os.listdir(namesfolder):
        if filename.endswith('.txt') and countrycode in filename:
            # Construct the full file path
            file_path = os.path.join(namesfolder, filename)

            # Open and read the file
            with open(file_path, 'r') as file:
                # Read the content and split by commas
                content = file.read().strip().split(', ')
                # Extend the big list with the content
                namelist.extend(content)
    if disp:
        print('satellite names for', countrycode, ' : \n', namelist)
    # in noinfo there is a list of conflicts that did not list a carrier frequency. these need to have the mission names
    # extracted and compared with the ones listed and output as noinfofoundmissionlist
    # 1 find all the names in noinfo
    noinfonames1 = noinfo[' com_el.sat_name'].unique()
    if disp:
        display(noinfo)
    noinfonames = []
    for n in noinfonames1:
        if n in namelist:
            noinfonames.append(n)
    if disp:
        print('names with no frequency info', noinfonames)  # todo return this

    ## extend the conflicts
    print('expanding the conflict columns for', countrycode)
    sleep(5)
    expanded, conflictcolumns = conflict_expander(conflicts, referencedf, eminames=True)

    ## filter by names
    # Isolate the lines where the name corresponds to one of the big list entries
    matched_df = expanded[expanded[' com_el.sat_name'].isin(namelist)]

    # Create the discarded dataframe with the remaining lines
    discarded_df = expanded[~expanded[' com_el.sat_name'].isin(namelist)]

    ## separate the conflicts in types
    # create directory if not exist
    os.makedirs(os.path.join(outfolder, 'output_tables'), exist_ok=True)
    conflict_tables_separator(matched_df, referencedf, os.path.join(outfolder, 'output_tables'))

    # save expanded to file
    matched_df.to_csv(os.path.join(outfolder, 'expanded_combined_tables_conflicts_lettersatnames.csv'), index=False)
    print('file saved to ', os.path.join(outfolder, 'expanded_combined_tables_conflicts_lettersatnames.csv'))
    discarded_df.to_csv(os.path.join(outfolder, 'expanded_combined_tables_conflicts_othersatnames.csv'), index=False)
    print('file saved to', os.path.join(outfolder, 'expanded_combined_tables_conflicts_othersatnames.csv'))

    return noinfonames
