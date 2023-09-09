from rules.persistence.file_system import LocalFileManager

import pandas
manager = LocalFileManager('dfdb')
reps = manager.download('representations.pkl')

l = list(map(lambda d : vars(d), reps))

print(pandas.DataFrame(l))
