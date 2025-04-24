_This project contains the tools to analyse the csv files produced by the ITU explorer query builder. The aim is to find
possible conflicts between existing missions and the TPA1 radio emissions._

# List of the scripts

## Germany example (proof of concept)

- **german_db_conflicts.ipynb**: this script needs to be run at least once to add the channel columns to the TPA filing
  table and provides an example to understand how a frequency overlap conflict is defined.
    - *inputs*
        1. 'TPAtable.csv' contains the filing of TPA1, on every line a channel characterised by: *emission type (E/R)*,
           *carrier frequency*, *emission code*
        2. 'germany.csv' contains the entries for germany with the same column structure of the TPA table.
    - *outputs*
        1. adds the channel columns (fmin and fmax for every carrier+emission code) to both TPA and germany csv tables
        2. adds the conflicts to germany as a list of numbers for every entry (row) each number representing an row
           index in the TPA table (conflict)

## Full coordination database

In the order they need to be run to reproduce the results

- **tpa_freq_extraction.ipynb**: takes the filing table for New Zealand and extracts the filing bands for TPA1 to be
  used in the space explorer query builder frequency filter section
- **sat_names_check.ipynb**: uses a soft matching algorithm to check if the names copied from the various administration
  letters are in the database.
    - *inputs*
        1. **folder** containing one .txt file per administration (./satellitenames) with a comma-separated list of all
           the
           satellite names (built from the Tracking spreadsheet)
        2. **folder** containing all the .csv filed downloaded from space explorer (./countriestables), one or more csv
           table per administration.
    - *outputs*
        1. **satellite_matches.csv**: 4 columns table, administration code, satellite name from the Tracking spreadsheet
           lists, best match found in the ITU tables, match score (0-100, with 100 exact match)
- **get_operator.ipynb**: specific for spain response, in the letter is written to check all satellites belonging to a
  specific company. Since there is no info in the ITU database regarding the company name, it was checked if the company
  name string is contained in the satellite name (a few matches were found this way).

- **conflicts_lister.ipynb**: actually finds the frequency emissions conflicts (carrier +- bandwidth, NOTE: <u>these are
  not the "frequency bands" from the filing as all the tables downloaded from the query builder is obtained by filtering
  for entries already within the TPA filing bands</u>) relative to every entry in every administration table
    - *inputs*
        1. **folder** containing one .txt file per administration (./satellitenames) with a comma-separated list of all
           the satellite names (built from the Tracking spreadsheet)
        2. **folder** containing all the .csv filed downloaded from space explorer (./countriestables), one or more csv
           table per administration.
        3. **TPAtable.csv** containing the filing for the TPA mission with the channel columns already appended (one row
           per emission containing type fmin and fmax)
    - *output*
        1. **combined_tables_conflicts.csv**: an agglomerate of all conflicting entries with reference to the
           conflicting TPA entries and the percentage of band overlap
- **conflicts_expander.ipynb**: takes the conflicts list in the table and separates the conflicts into individual extra
  columns each one for a separate conflict type over a certain channel (12 channels in total over 2 S bands and 1 UHF
  band):
    - *inputs*:
        1. **combined_tables_conflicts.csv**: from conflicts_lister.ipynb
        2. **TPAtable.csv**: from tpa_freq_extraction.ipynb
    - *outputs*:
        1. **expanded_combined_tables_conflicts.csv**: same table of combined_tables_conflicts.csv, but with extra
           columns each containing a single overlap percentage for a single conflict type and channel. contains only the
           entries with satellite name contained in the ./satellitenames folder
        2. **expanded_combined_tables_conflicts_rejected**: conflict table for all the satellite names not in the lists
        3. **output_tables folder**: containing the output tablse separated by conflict type and channel
- **big_script.ipynb** create a folder for each administration
- **summary table.ipynb** creates the conflicts_summary in each adm folder
# Functions in ITUtils.py

ITUtils.py contains a series of functions to perform the frequency overlap and percentage of overlap checks on the
tables.

- **itu_to_bandwidth(itu_designation)**: Converts ITU designation of emission to bandwidth in Hz.
- **channel_appender(df)**: Appends channel bandwidth, frequency minimum, and frequency maximum to the dataframe.
- **conflicts_appender(targetdf, referencedf)**: Identifies and appends conflicts between target and reference
  dataframes.
- **conflict_expander(ddf_conflicts, referencedf)**: Expands conflict details and appends specific conflict information
  to the dataframe.
- **conflict_tables_separator(expanded, reference_df, outfolder)**: from the expanded conflict table generates a table
  for each conflict type, for each TPA channel. It also produces reduced tables with only one entry per satellite name (
  with the highest frequency overlap percentage). used in 'conflicts_expander.ipynb'

# Conflict types

A conflict is here defined as a partial or total overlap of a foreign satellite channel i.e. the carrier frequency +-
the bandwidth defined by the ITU emission code of the table entry with one of the channels of the TPA1 filing.
For every TPU channel i.e.

| ID | Receive/Emit | NAME  | emi_des   | f_carrier |
|----|--------------|-------|-----------|-----------|
| 0  | R            | UHFUP | 9K50F1DAN | 401.96    |
| 1  | R            | UHFUP | 19K8F1DAN | 401.96    |
| 2  | R            | SUP   | 250KM1DAN | 2055.6    |
| 3  | R            | UHFUP | 9K50F1DAN | 401.9     |
| 4  | E            | SDN   | 1M00M1DAN | 2237.5    |
| 5  | R            | SUP   | 250KM1DAN | 2065.7    |
| 6  | E            | UHFDN | 19K8F1DAN | 401.96    |
| 7  | R            | UHFUP | 19K8F1DAN | 401.9     |
| 8  | E            | UHFDN | 9K50F1DAN | 401.96    |
| 9  | E            | UHFDN | 19K8F1DAN | 401.9     |
|10  | E            | UHFDN | 9K50F1DAN | 401.9     |
|11  | E            | SDN   | 1M00M1DAN | 2202.9    |


The conflicts can be of the kind
1. **ER** TPA emitting, Other receiving (interference over foreign satellite)
2. **EE** TPA emitting, Other emitting (interference over foreign base station)
3. **RR** TPA receiving, Other receiving (interference over foreign satellite)
4. **RE** TPA receiving, Other emitting (interference over TPA satellite -- NOT A PROBLEM)

as a result in the 'output_tables' folder there will be 24 files for the emission-to-emission line conflicts 
and other 24 files for the simplified case with only the worst case overlap per each satellite name.
# Required input files

- **./satellitenames/*.txt**: set of txt files containing the satellite namesas comma separated lists
- **./countriestables/*.csv**: set of csv files downloaded from the query builder in space explorer (see bookmarked
  queries for selected datafields)
- **./databses/NZquery.csv**: same table of other countries but for new zealand

# Summary of Generated Tables for Coordination

- **Table of Name Matches**: 'satellite_matches.csv': Contains a 4 columns table, administration code, satellite name
  from the Tracking spreadsheet lists, best match found in the ITU tables, match score (0-100, with 100 exact match)

IN FOLDER ./databses/
- **Expanded Conflict Table**: 'expanded_combined_tables_conflicts.csv': Contains the original conflict data with
  additional columns for each conflict type and channel.
- **Rejected entries Table**: 'expanded_combined_tables_conflicts_rejected.csv' : Contains all the conflicts that do not
belong to any of the listed satellite names.

IN FOLDER ./output_tables/ 
- **Separated Conflict Tables**: Files like TPA1.2055.475-2055.725_R_E.csv: Each file contains data for a specific
  conflict type and frequency range.

- **Worst-case Scenario Tables**:
  Files like TPA1.2055.475-2055.725_R_E_worstcase.csv: Each file contains the worst-case frequency overlap percentage
  for each mission within the specified conflict type and frequency range.


