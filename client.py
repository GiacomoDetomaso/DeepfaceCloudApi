import pickle
import pandas

with open('dfdb/representations.pkl', 'rb') as f:
    reps = pickle.loads(f.read())

l = []
for r in reps:
    l.append(vars(r))

print('M' in pandas.DataFrame(l)['username'].values)