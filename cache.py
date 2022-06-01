
import os, shutil, hashlib, datetime, numpy as np

class cache:
  def __init__(self, parameters, force=False):
    assert(set(self.requires()) == set(parameters)) # validate all parameters were passed
    h = hashlib.sha256()
    h.update(self.id(parameters).encode()) # get the unique cache identifier
    cache_id = h.hexdigest() # generate hash id for cache file
    results = {"cache_id": cache_id, "object": {}} # populate empty cache
    cache_path = "caches"
    if not os.path.isdir(cache_path):
      os.mkdir(cache_path)
    file_path = "%s/%s.npy" % (cache_path, cache_id)
    backup_path = file_path + ".tmp" # backup any existing cache file
    if os.path.isfile(file_path) and not force: # load cache is it exists
      try:
        results = np.load(file_path, allow_pickle=True).tolist()
      except:
        results = np.load(backup_path, allow_pickle=True).tolist()
        np.save(file_path, results) # commit cache to disk
      assert(results["cache_id"] == cache_id) # confirm the loaded object is the expected object
    self.process(parameters, results["object"])
    if os.path.isfile(file_path):
      shutil.copyfile(file_path, backup_path)
    np.save(file_path, results) # commit cache to disk
    self.object = results["object"] # save cache internally

  def requires(self):
    assert(False) # must be overridden

  def id(self, parameters):
    assert(False) # must be overridden

  def process(self, parameters, o):
    assert(False) # must be overridden
