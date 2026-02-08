# signalis_experiment_scraper
Custom-built scraper using Revvity Signalis API

We are using the search feature of the API to grab and auto-fill a .csv with data from Experiments that match a given keyword.

/entities/search - grabs all experiment IDs {eid}s
/stoichiometry/{eid} - grabs all information about the given experiment

From each experiment, we are retrieving the following:
This first five are "per experiment":
* source_id - Experiment name
* temperature_deg_c - /conditions attributes conditions temp (remove unit)
* time_h - /conditions attributes conditions duration
* scale_mol - Limit Moles converted to moles !unit
* concentration_mol_l - [summary][limitingmolarity]
The rest are "per row". Repeat as necessary for # of solvents/catalysts/products:
* solvent_#_cas - /solvents attributes solvent name
* catalyst_#_name - /stoichiometry attributes name
* catalyst_#_cas - /stoichiometry attributes iupac name
* catalyst_#_smiles - /stoichiometry/{cdid}/{rowid}/structure?format=smiles
* catalyst_#_eq - /stoichiometry attributes eq
* product_#_smiles - /products smiles (see if ?format=smiles exists)
* product_#_yield - round to whole #, remove the %