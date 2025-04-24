
# adm_conflicts Folder

This folder contains the output conflict analysis results, separated by administration (adm code).

## File Structure

For each administration (e.g., `AUS`, `CAN`, `CHN`, etc.), the following files are produced:

- **conflicts.csv**  
  Full list of conflicts found, one row per conflict event.

- **expanded_combined_tables_conflicts_lettersatnames.csv**  
  Conflicts only for satellites listed in the administration-provided name lists.

- **expanded_combined_tables_conflicts_othersatnames.csv**  
  Conflicts for satellites not present in the administration-provided lists.

- **conflict_percent_pivot_table.csv**  
  Pivot table summarizing percentage overlaps by satellite name and TPA channel.
  NOTE: the percent is defined as band_overlap / foreign_sat_bandwidth x 100 

- **conflict_summary_by_freq_type.csv**  
  Summary table aggregating conflicts by frequency range and conflict type (e.g., E_R, R_E, etc.). The frequency and bandwidth columns refer to the TPA1 mission filings

- **conflict_type_barplot.png**  
  Bar plot showing the number of conflicts per conflict type.

- **noinfooncarrierfrequency.txt**  
  List of entries where carrier frequency information was missing or incomplete.

- **output_tables**  
  Folder containing conflict tables split by TPA1 channel and conflict type, plus worst-case overlap summaries.

- **conflicts_summary**
  Contains a table with entries for all the satellite names (from the adm. letters). It contains the following 5 columns:  Sat Name (=com_el.sat_name), Beam Name (=s_beam.beam_name), Carrier Freq. (fc) (=carrier_fr.freq_carrier), Bandwidth ( from emiss.design_emi), Overlaps (list of overlapping TPA channels) 
