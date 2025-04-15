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

- **tpa_freq_extraction.ipynb**: takes the filing table for New Zealand and extracts the filing bands for TPA1 to be
  used in the space explorer query builder frequency filter section
- **sat_names_check.ipynb**: uses a soft matching algorithm to check if the names copied from the various administration
  letters are in the database.
    - *inputs*
        1. **folder** containing one .txt file per administration (./satellitenames) with a comma-separated list of all the
           satellite names (built from the Tracking spreadsheet)
        2. **folder** containing all the .csv filed downloaded from space explorer (./countriestables), one or more csv
           table per administration.
    - *outputs*
        1. **satellite_matches.csv**: 4 columns table, administration code, satellite name from the Tracking spreadsheet
           lists, best match found in the ITU tables, match score (0-100, with 100 exact match)
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
        1. **combined_tables_conflicts.csv**: an agglomerate of all conflicting entries
- **get_operator.ipynb**: specific for spain response, in the letter is written to check all satellites belonging to a
  specific company. Since there is no info in the ITU database regarding the company name, it was checked if the company
  name string is contained in the satellite name (a few matches were found this way).

# Functions in ITUtils.py

ITUtils.py contains a series of functions to perform the frequency overlap and percentage of overlap checks on the
tables.

- **itu_to_bandwidth(itu_designation)**: Converts ITU designation of emission to bandwidth in Hz.
- **channel_appender(df)**: Appends channel bandwidth, frequency minimum, and frequency maximum to the dataframe.
- **conflicts_appender(targetdf, referencedf)**: Identifies and appends conflicts between target and reference
  dataframes.
- **conflict_expander(ddf_conflicts, referencedf)**: Expands conflict details and appends specific conflict information
  to the dataframe.
