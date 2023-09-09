import pickle
import pandas

from rules.blobs import AzureBlobManager

from firebase_admin import initialize_app
from firebase_admin import firestore
from google.cloud.firestore_v1.client import Client

manager = AzureBlobManager('dfdb')
reps = manager.download('representations.pkl')

l = []
for r in reps:
    l.append(vars(r))

print(pandas.DataFrame(l))

