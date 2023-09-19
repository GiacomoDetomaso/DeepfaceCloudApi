from rules.persistence.local import LocalFileManager
from rules.persistence.azure import AzureBlobManager
from rules.persistence.firestore import FirestoreDatabaseManager

import pandas

manager = AzureBlobManager('dfdb')
reps = manager.download('representations.pkl')

l = list(map(lambda d : vars(d), reps))

manager = FirestoreDatabaseManager()
manager.upload('representations', l)