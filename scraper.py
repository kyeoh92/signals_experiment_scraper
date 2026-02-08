from logging import root
import re
from urllib import response
import requests
import subprocess

url = "https://ucberkeleysite.signalsresearch2.revvitycloud.com/api/rest/v1.0"
apikey = "WPN8LoLt+odVKIM+D9RI89kcp/JjYWj2fUKylJLzeAts0JJ5fCnOjTGZrlm9/vVMNBRs4w=="
authHeader = {"Content-Type":"application/vnd.api+json","x-api-key":apikey}

# Helper methods
# region

# trim everything but numbers from string
def trimToNumbers(s):
    return re.sub(r'\D', '', s)

# print [][]s to .csv
def writeToCSV(rows, filename='output'):
    with open(filename+'.csv', 'w') as f:
        for row in rows:
            f.write('|'.join(row) + '\n')

# endregion

# API methods
# region
# Get all experiment IDs with keyword in their description
def getAllExperimentIDs(keyword):
    eids = []
    data =  {
            "query": {
                "$and": [
                  {
                    "$match": {
                      "field": "type",
                      "value": "experiment",
                      "mode": "keyword"
                    }
                  },
                  {
                    "$match": {
                      "field": "description",
                      "value": keyword
                    }
                  }
                ]
              }
            }

    response = requests.post(url+"/entities/search", headers=authHeader, json=data)
    responseData = response.json()

    for e in responseData['data']:
        eids.append(e['attributes']['name'] +'|' + e['id'])

    return eids

# Process reactant to grab smile strings
def getSmilesFromChemDraw(rowid, eid):
    response = requests.get(url+"/stoichiometry/{eid}/{rowid}/structure?format=smiles".format(eid=eid, rowid=rowid), headers=authHeader)
    return response.text

# Get all .csv row data from all experiments with keyword in their description
def getAllStoichiometry(keyword):
    eids = getAllExperimentIDs(keyword)

    csvRows = []
    solventCount, catalystCount, productCount = 0, 0, 0 # variables to keep track of how many catalysts and products

    for e in eids:
        eid = e.split('|')[1] # grab experiment ID from "name|experimentID" string
        response = requests.get(url+"/stoichiometry/"+eid, headers=authHeader)
        responseData = response.json()

        conditions = responseData['data'][0]['attributes']['conditions'][0]
        summary = responseData['data'][0]['attributes']['summary']
        solvents = responseData['data'][0]['attributes']['solvents']
        reactants = responseData['data'][0]['attributes']['reactants']
        products = responseData['data'][0]['attributes']['products']
        included = responseData['included']
        userColKey = ''

        for i in included:
            if i.get("type") == "columnDefinitions":
                productColumnDefinitions = i['attributes']['products']
                for pcd in productColumnDefinitions:
                    if pcd.get("title") == "user_column":
                        userColKey = pcd.get("key", '')

        solventCount = len(solvents)
        catalystCount = len(reactants)
        productCount = len(products)

        csvRow = [] # object to store row to write to .csv
        csvRow.append(e.split('|')[0]) # append source_id

        # conditions 
        csvRow.append(trimToNumbers(conditions.get('temperature', ''))) # append temperature_deg_c
        csvRow.append(trimToNumbers(conditions.get('duration', ''))) # append time_h

        # summary
        csvRow.append(trimToNumbers(summary.get('limitingMolarity', ''))) #append scale_mol
        csvRow.append(trimToNumbers(summary.get('reactionMolarity', ''))) #append concentration_mol_l

        # solvents
        for s in solvents:
            csvRow.append(s.get('solvent', '')) # append solvent_#_cas

        # reactants
        for r in reactants:
            csvRow.append(r.get('name', '')) # append catalyst_#_name
            csvRow.append(r.get('IUPACName', '')) # append catalyst_#_cas
            csvRow.append(getSmilesFromChemDraw(r['row_id'], eid)) # append catalyst_#_smiles
            csvRow.append(r.get('eq', '')) # append catalyst_#_eq

        # products
        for p in products:
            csvRow.append(getSmilesFromChemDraw(p['row_id'], eid)) # append product_#_smiles
            csvRow.append(trimToNumbers(p.get('yield', ''))) # append product_#_yield
            csvRow.append(p.get(userColKey, '')) # append product_#_user_column

        csvRows.append(csvRow)

    # write header row, done last after counting # solvents/catalysts/products
    headerRow = [] # object to store header row to write to .csv
    headerRow.append('source_id')
    headerRow.append('temperature_deg_c')
    headerRow.append('time_h')
    headerRow.append('scale_mol')
    headerRow.append('concentration_mol_l')
    for i in range(1, solventCount+1):
        headerRow.append('solvent_'+str(i)+'_cas')
    for i in range(1, catalystCount+1):
        headerRow.append('catalyst_'+str(i)+'_name')
        headerRow.append('catalyst_'+str(i)+'_cas')
        headerRow.append('catalyst_'+str(i)+'_smiles')
        headerRow.append('catalyst_'+str(i)+'_eq')
    for i in range(1, productCount+1):
        headerRow.append('product_'+str(i)+'_smiles')
        headerRow.append('product_'+str(i)+'_yield')
        headerRow.append('product_'+str(i)+'_user_column')

    csvRows.insert(0, headerRow)
    return csvRows
# endregion

# outdated obabel commands
# region 
# Create InChi files from InChi strings
# def writeInChisToFile(inchis):
#     for i, inchi in enumerate(inchis):
#         with open(f"molecule_{i}.inchi", "w") as f:
#             f.write(inchi)

# Get all CDXMLs from all experiments with keyword in their description
# def getAllCDXMLs(keyword):
#     eids = getAllExperimentIDs(keyword)
#     cdxmls = []
#     for eid in eids:
#         response = requests.get(url+"/stoichiometry/"+eid, headers=authHeader)
#         responseData = response.json()
#         reactantsData = responseData['data'][0]['attributes']['reactants']
#         for r in reactantsData:
#             cdxmls.append(r['_cdxml'])
#         
#     return cdxmls

# Create CDXML files from CDXML strings
# def writeXMLFiles(xmls):
#     for i, xml in enumerate(xmls):
#         with open(f"molecule_{i}.cdxml", "w") as f:
#             f.write(xml)

# Use command line OpenBabel to convert from CDXML to SMILES string
# def runCmdLineConversionCDXMLtoMOLtoSMI(xmlFile):
#     molFile = xmlFile.replace('.cdxml', '.mol')
#     cmd = f"obabel -icdxml {xmlFile} -omol -O {molFile}"
#     subprocess.run(cmd, shell=True)
#     cmd2 = f"obabel -imol {molFile} -osmi -O {xmlFile.replace('.cdxml', '.smi')}"
#     subprocess.run(cmd2, shell=True)

# Use command line OpenBabel to convert from InChi to SMILES string
# def runCmdLineConversionInChitoSMI(inputFile, outputFile):
#     cmd = f"obabel -iinchi {inputFile} -osmi -O {outputFile}"
#     subprocess.run(cmd, shell=True)
# endregion

searchKeyword = input("Keyword? ")
csvRows = getAllStoichiometry(searchKeyword)
print(csvRows)
writeToCSV(csvRows, searchKeyword)