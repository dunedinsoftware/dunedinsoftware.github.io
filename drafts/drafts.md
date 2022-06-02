Something we haven't done is to back out a drift component $d$ from the T. Assume:

  $$chunk\enspace size = \lambda T + c $$

then solve for $c$ in $T_{ret}$ and $T_{all}$, disregarding $\lambda$, leaving:
  
  $$d = 1.0 - \frac{c_{ret}}{c_{all}}$$

which comes out as $\approx$ 0.21 for GSPC.

```
def drift_factor(symbol_path):
  retain = 0.1 # top 10% of chunks by trendiness
  results, dfl = [], data_file_loader({"path": symbol_path})
  returns = [dfl.series[dt]["next_delta"] for dt in dfl.s_dates]
  for chunk_size in range(10, 100, 1):
    chunks = [returns[i:i+chunk_size] for i in range(0, len(returns), chunk_size)]
    samples = [{"train": trendiness(chunks[train_index]), "test": trendiness(chunks[train_index+1])} for train_index in range(len(chunks)-1)]
    df_all = pd.DataFrame(samples).sort_values(by=["train"], ascending=False)
    t_null = np.corrcoef(df_all["train"], df_all["test"])[0][1]
    df = df_all[0:int(len(samples) * retain)]
    t = np.corrcoef(df["train"], df["test"])[0][1]
    results.append({"chunk_size": chunk_size, "trendiness": t, "t_null": t_null, "n": len(samples)})
  df_results = pd.DataFrame(results).dropna()
  _, c_null = np.polyfit(df_results["chunk_size"], df_results["t_null"], deg=1)
  _, c_1 = np.polyfit(df_results["chunk_size"], df_results["trendiness"], deg=1)
  d = abs(c_all) / (abs(c_1) + abs(c_null))
```
