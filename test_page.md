layout: page
title: "My test page"

## This is a subtitle
Here is some text

```
def process(dict, min_n=30):
  dates, values = sorted(dict.keys()), {0, 1}
  indices = {key : [] for key in values}
  for i in range(1, len(dates)): indices[dict[dates[i]]].append(i) # indices by key
  models = [] 
  unprocessed = [{"state": 0, "next": None, "prior": set([i for i in range(len(dates)-1)]), "p": 0}] # all indices
  while len(unprocessed):
    m = unprocessed.pop() # current set
    models.append(m)
    if len(m["prior"]) >= min_n:
      m0 = {"state": 0, "next": m, "prior": set([j-1 for j in m["prior"] if dict[dates[j-1]] == 0]), "p": 0, "prev": []} # prior zeroes
      m1 = {"state": 1, "next": m, "prior": set([j-1 for j in m["prior"] if dict[dates[j-1]] == 1]), "p": 0, "prev": []} # prior ones
      m["p"] = len(m1["prior"]) / (len(m0["prior"]) + len(m1["prior"])) # p(m) was caused by 1
      m["prev"] = [m0, m1]
      unprocessed += [m0, m1]      
  return models
```
