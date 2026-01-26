from logging import root
import requests
import subprocess

url = "https://ucberkeleysite.signalsresearch2.revvitycloud.com/api/rest/v1.0"
apikey = "WPN8LoLt+odVKIM+D9RI89kcp/JjYWj2fUKylJLzeAts0JJ5fCnOjTGZrlm9/vVMNBRs4w=="
authHeader = {"Content-Type":"application/vnd.api+json","x-api-key":apikey}


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
        eids.append(e['id'])
    
    return eids

# Get all InChi stoichiometry from all experiments with keyword in their description
def getAllStoichiometry(keyword):
    eids = getAllExperimentIDs(keyword)

    inchis = []
    for eid in eids:
        response = requests.get(url+"/stoichiometry/"+eid, headers=authHeader)
        responseData = response.json()
        reactants = responseData['data'][0]['attributes']['reactants']
        for r in reactants:
            inchis.append(r['inchi'])
        
    return inchis

# Create InChi files from InChi strings
def writeInChisToFile(inchis):
    for i, inchi in enumerate(inchis):
        with open(f"molecule_{i}.inchi", "w") as f:
            f.write(inchi)

# Get all CDXMLs from all experiments with keyword in their description
def getAllCDXMLs(keyword):
    eids = getAllExperimentIDs(keyword)

    cdxmls = []
    for eid in eids:
        response = requests.get(url+"/stoichiometry/"+eid, headers=authHeader)
        responseData = response.json()
        reactantsData = responseData['data'][0]['attributes']['reactants']
        for r in reactantsData:
            cdxmls.append(r['_cdxml'])
        
    return cdxmls

# Create CDXML files from CDXML strings
def writeXMLFiles(xmls):
    for i, xml in enumerate(xmls):
        with open(f"molecule_{i}.cdxml", "w") as f:
            f.write(xml)

# Use command line OpenBabel to convert from CDXML to SMILES string
def runCmdLineConversionCDXMLtoMOLtoSMI(xmlFile):
    molFile = xmlFile.replace('.cdxml', '.mol')
    cmd = f"obabel -icdxml {xmlFile} -omol -O {molFile}"
    subprocess.run(cmd, shell=True)
    cmd2 = f"obabel -imol {molFile} -osmi -O {xmlFile.replace('.cdxml', '.smi')}"
    subprocess.run(cmd2, shell=True)

# Use command line OpenBabel to convert from InChi to SMILES string
def runCmdLineConversionInChitoSMI(inputFile, outputFile):
    cmd = f"obabel -iinchi {inputFile} -osmi -O {outputFile}"
    subprocess.run(cmd, shell=True)

searchKeyword = input("Keyword? ")
inchis = getAllStoichiometry(searchKeyword)
writeInChisToFile(inchis)

writeXMLFiles(getAllCDXMLs(searchKeyword))

for i in range(len(inchis)):
    runCmdLineConversionInChitoSMI(f"molecule_{i}.inchi", f"molecule_{i}.smi")