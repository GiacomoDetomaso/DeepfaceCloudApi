import pickle
import pandas

from rules.persistence import AzureBlobManager

from firebase_admin import initialize_app
from firebase_admin import firestore
from google.cloud.firestore_v1.client import Client

manager = AzureBlobManager('dfdb')
reps = manager.download('representations.pkl')

l = list(map(lambda d : vars(d), reps))

print(pandas.DataFrame(l))

