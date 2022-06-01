
import os, datetime
from cache import cache

class data_directory_loader(cache):
  series, symbols, s_dates, dtoi, itod = None, None, None, None, None # expose so clients know what properties exist on this object

  def __init__(self, parameters, force=False):
    super().__init__(parameters, force) # load cache if present, update and commit

  def requires(self):
    return ["path"]

  def id(self, parameters):
    return "prices-%s" % parameters["path"]

  def update_file_read_offset(self, f, headers, dt):
    chunk_size, offset = 256, 256
    f.seek(0, os.SEEK_END)
    eof_offset = f.tell()
    while True:
      f.seek(eof_offset - offset)
      line = f.readline() # potentially line fragment
      line = f.readline() # whole line
      tokens = line.split(',')
      s_dt = datetime.datetime.strptime(tokens[headers.index("Date")].strip(), "%Y-%m-%d")
      if s_dt < dt:
        break
      offset += chunk_size
    return f

  def process(self, parameters, o):
    data_in_cache, files_in_cache, symbols, s_dates, dtoi, itod, directory = {}, set(), set(), set(), {}, {}, parameters["path"]
    if len(o) == 0:
      o["data"], o["files"], o["symbols"], o["s_dates"], o["dtoi"], o["itod"] = data_in_cache, files_in_cache, symbols, s_dates, dtoi, itod
    else:
      data_in_cache, files_in_cache, symbols, s_dates, dtoi, itod = o["data"], o["files"], o["symbols"], o["s_dates"], o["dtoi"], o["itod"]
    files_on_disk = ["%s/%s" % (directory, symbol) for symbol in os.listdir(directory) if symbol.endswith(".csv") and "VIX" not in symbol]
    recalc_all = False # if a file on disk has been deleted, we need to recalculate all of s_dates, dtoi, etc.
    for file_to_delete in [q for q in files_in_cache if q not in files_on_disk]:
      recalc_all = True
      files_in_cache.remove(file_to_delete)
      symbol_to_delete = file_to_delete.split('/')[-1]
      for k in [q for q in data_in_cache.keys() if symbol_to_delete in data_in_cache[q].keys()]:
        data_in_cache[k].pop(symbol_to_delete) # remove entry from cache for symbol and date
        if len(data_in_cache[k].keys()) == 0:
          data_in_cache.pop(k) # remove the date if it no longer has any symbols associated with it
    files_in_cache.clear() # clear to retain object reference in cache (will re-populate below)
    symbols.clear() # clear to retain object reference in cache (will repopulate below)
    if recalc_all:
      s_dates.clear() # clear, since removing a symbol may change the set of dates stored
      dtoi.clear() # ditto
      itod.clear() # ditto
    for cur_file in files_on_disk:
      symbol = cur_file.split('/')[-1]
      symbols.add(symbol)
      files_in_cache.add(cur_file)
      deltas = {} # dictionary of delta updates to apply to the other data structures
      symbol_dates = [q for q in data_in_cache.keys() if symbol in data_in_cache[q].keys()]
      with open(cur_file, "r") as f:
        headers = f.readline().strip().split(',')
        if len(symbol_dates) > 0 and not recalc_all:
          self.update_file_read_offset(f, headers, max(symbol_dates) - datetime.timedelta(days=5)) # last known date for symbol in cache
        for line in f.readlines():
          tokens = line.split(',')
          s_dt = datetime.datetime.strptime(tokens[headers.index("Date")].strip(), "%Y-%m-%d")
          if s_dt not in data_in_cache.keys():
            data_in_cache[s_dt] = {}
          s_adj_close = float("%.8f" % float(tokens[headers.index("Adj Close")].strip()))
          s_close = float("%.8f" % float(tokens[headers.index("Close")].strip()))
          s_high = float("%.8f" % float(tokens[headers.index("High")].strip()))
          s_low = float("%.8f" % float(tokens[headers.index("Low")].strip()))
          s_open = float("%.8f" % float(tokens[headers.index("Open")].strip()))
          s_volume = float("%.8f" % float(tokens[headers.index("Volume")].strip()))
          if s_close != 0 and s_dt.weekday() < 5: # drop empty prices and weekends
            deltas[s_dt] = {"adj close": s_adj_close, "close": s_close, "open": s_open, "high": s_high, "low": s_low, "volume": s_volume}
      delta_dates = sorted(deltas.keys()) # apply the deltas to the various data structures
      for i in range(0, len(delta_dates)):
        cur_dt, prev_dt, next_dt = delta_dates[i], delta_dates[max(0, i-1)], delta_dates[min(len(delta_dates)-1, i+1)]
        data_in_cache[cur_dt][symbol] = cur_o = deltas[cur_dt]
        data_in_cache[prev_dt][symbol] = prev_o = deltas[prev_dt]
        data_in_cache[next_dt][symbol] = next_o = deltas[next_dt]
        cur_o["prev_close"], cur_o["next_close"] = prev_o["close"], next_o["close"]
        cur_o["prev_delta"], cur_o["next_delta"] = (cur_o["close"] / cur_o["prev_close"]) - 1.0, (cur_o["next_close"] / cur_o["close"]) - 1.0
        if cur_dt not in s_dates:
          s_dates.add(cur_dt)
    sorted_dates = sorted(s_dates) # s_dates is a set, so doesn't have a "sort" method
    for i in range(len(sorted_dates)): # always recreate dtoi and itod for the full set of dates
      dtoi[sorted_dates[i]], itod[i] = i, sorted_dates[i]
    self.series, self.symbols, self.s_dates, self.dtoi, self.itod = data_in_cache, symbols, sorted_dates, dtoi, itod 

class data_file_loader(cache):
  series, s_dates, dtoi, itod = None, None, None, None # expose so clients know what properties exist on this object

  def __init__(self, parameters, force=False):
    super().__init__(parameters, force) # load cache if present, update and commit

  def requires(self):
    return ["path"]

  def id(self, parameters):
    return "prices-%s" % parameters["path"]

  def update_file_read_offset(self, f, headers, dt):
    chunk_size, offset = 256, 256
    f.seek(0, os.SEEK_END)
    eof_offset = f.tell()
    while True:
      f.seek(eof_offset - offset)
      line = f.readline() # potentially line fragment
      line = f.readline() # whole line
      tokens = line.split(',')
      s_dt = datetime.datetime.strptime(tokens[headers.index("Date")].strip(), "%Y-%m-%d")
      if s_dt < dt:
        break
      offset += chunk_size
    return f
    
  def process(self, parameters, o):
    data_in_cache, s_dates, dtoi, itod = {}, set(), {}, {}
    if len(o) == 0:
      o["data"], o["s_dates"], o["dtoi"], o["itod"] = data_in_cache, s_dates, dtoi, itod
    else:
      data_in_cache, s_dates, dtoi, itod = o["data"], o["s_dates"], o["dtoi"], o["itod"]
    deltas = {} # dictionary of delta updates to apply to the other data structures
    with open(parameters["path"], "r") as f:
      headers = f.readline().strip().split(',')
      last_date = sorted(data_in_cache.keys())[-1] if len(data_in_cache.keys()) > 0 else None
      if last_date:
        self.update_file_read_offset(f, headers, last_date - datetime.timedelta(days=5)) # last known date in cache
      for line in f.readlines():
        tokens = line.split(',')
        s_dt = datetime.datetime.strptime(tokens[headers.index("Date")].strip(), "%Y-%m-%d")
        if s_dt not in data_in_cache.keys():
          data_in_cache[s_dt] = {}
        if len([q for q in tokens if len(q) == 0]) > 0:
          print("Skipping invalid data: %s" % line)
          continue
        s_adj_close = float("%.8f" % float(tokens[headers.index("Adj Close")].strip()))
        s_close = float("%.8f" % float(tokens[headers.index("Close")].strip()))
        s_high = float("%.8f" % float(tokens[headers.index("High")].strip()))
        s_low = float("%.8f" % float(tokens[headers.index("Low")].strip()))
        s_open = float("%.8f" % float(tokens[headers.index("Open")].strip()))
        s_volume = float("%.8f" % float(tokens[headers.index("Volume")].strip()))
        if s_close != 0 and s_dt.weekday() < 5: # drop empty prices and weekends
          deltas[s_dt] = {"adj close": s_adj_close, "close": s_close, "open": s_open, "high": s_high, "low": s_low, "volume": s_volume}
    delta_dates = sorted(deltas.keys()) # apply the deltas to the various data structures
    for i in range(0, len(delta_dates)):
      cur_dt, prev_dt, next_dt = delta_dates[i], delta_dates[max(0, i-1)], delta_dates[min(len(delta_dates)-1, i+1)]
      data_in_cache[cur_dt] = cur_o = deltas[cur_dt]
      data_in_cache[prev_dt] = prev_o = deltas[prev_dt]
      data_in_cache[next_dt] = next_o = deltas[next_dt]
      cur_o["prev_close"], cur_o["next_close"] = prev_o["close"], next_o["close"]
      cur_o["prev_delta"], cur_o["next_delta"] = (cur_o["close"] / cur_o["prev_close"]) - 1.0, (cur_o["next_close"] / cur_o["close"]) - 1.0
      if cur_dt not in s_dates:
        s_dates.add(cur_dt)
    sorted_dates = sorted(s_dates) # s_dates is a set, so doesn't have a "sort" method
    for i in range(len(sorted_dates)): # always recreate dtoi and itod for the full set of dates
      dtoi[sorted_dates[i]], itod[i] = i, sorted_dates[i]
    self.series, self.s_dates, self.dtoi, self.itod = data_in_cache, sorted_dates, dtoi, itod 
