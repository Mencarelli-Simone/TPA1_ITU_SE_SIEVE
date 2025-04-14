This project contains the tools to analyse the csv files produced by the ITU explorer query builder.
The aim is to find possible conflicts between existing missions and the TPA1 radio emissions.

# List of the scripts
## Germany example (proof of concept)

- **german_db_conflicts.ipynb**: this script needs to be run at least once to add the channel columns to the TPA filing table and provides an example to understand how a frequency overlap conflict is defined.
  - *inputs* 
    1. 'TPAtable.csv' contains the filing of TPA1, on every line a channel characterised by:
        *emission type (E/R)*, *carrier frequency*, *emission code*
    2. 'germany.csv' contains the entries for germany with the same column structure of the TPA table.
  - *outputs*
    1. adds the channel columns (fmin and fmax for every carrier+emission code) to both TPA and germany csv tables
    2. adds the conflicts to germany as a list of numbers for every entry (row) each number representing an row index in the TPA table (conflict) 
## Full coordination database
- **tpa_freq_extraction.ipynb**: todo
- **sat_names_check.ipynb**: todo
- **conflicts_lister.ipynb**: todo
  - *output* 
    1. 'combined_tables_conflicts.csv': todo explain
- **get_operator.ipynb**: specific for spain response. todo
# Functions in ITUtils.py
ITUtils.py contains a series of functions to perform the frequency overlap and percentual of overlap checks on the tables.
- todo