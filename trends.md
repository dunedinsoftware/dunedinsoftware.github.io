
# The Mystery of Trends
People talk about things they call "trends." Two things therefore concern us:
- Are trends coherent? Do they really exist? In other words, can we *define* what a trend actually is, and find evidence of such a thing?
- If so, can we predict the onset of a trend?

To answer the first question we need to define what a trend is. We have many options, but most simply we might try:

<div align="center"><img src="article_1/formula_1.png" height=64/></div>

<span hidden>
$$T = \frac{\lvert \sum_{t=0}^{n}r_t \rvert}{\sum_{t=0}^{n}\lvert r_t \rvert} $$
</span>

with

<div align="center"><img src="article_1/formula_2.png"/></div>

<span hidden>
$$
\begin{equation}
{r_t} = \frac{p_t}{p_t-1}-1
\enspace,\enspace {P} = \{p_0, p_1, p_2, \dots \enspace p_n \in R \enspace | \enspace p_t > 0\}, \enspace p_t \in P
\end{equation}
$$
</span>


In other words trendiness is a coefficient corresponding to the ratio of signed to unsigned returns over a set of prices *P*. 

Now if we go with this definition then the trendiness of the full series isn't of interest to us, because it disproportionately depends upon p<sub>0</sub> and p<sub>n</sub>, and if these happen to be the same then *T* = 0 regardless of the price evolution. Rather, we are interested in identifying smaller trends somewhere within it. So need to break up the price data into chunks and check each of these for trendiness. We have not defined what *T* constitutes a trend and would prefer not to introduce a specific constraint, since the choice is essentially arbitrary. Similarly, we don't know what chunk size *n* might be important, so we will investigate the range *[10, 100]*.

We therefore proceed as follows:
- split the data into consecutive same-size chunks of training and test data
- calculate *T* for the training chunks, and discard the smallest 90% of such samples
- calculate the correlation of T<sub>train</sub> to T<sub>test</sub> for the remaining data

```
# our trendiness lambda
trendiness = lambda chunk: abs(sum(chunk)) / np.sum([abs(r) for r in chunk])

def test_stationarity(symbol):
  results, retain, data = [], 0.1, yf.download(symbol, start="2005-01-03")
  data["r"] = data["Close"].pct_change()
  data = data[data["r"].notna()]
  for chunk_size in range(10, 100, 1):
    chunks = [data["r"][i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    samples = [{"train": trendiness(chunks[train_index]), "test": trendiness(chunks[train_index+1])} for train_index in range(len(chunks)-1)]
    df = pd.DataFrame(samples).sort_values(by=["train"], ascending=False)[0:int(len(samples) * retain)]
    results.append({"chunk_size": chunk_size, "trendiness": np.corrcoef(df["train"], df["test"])[0][1], "n": len(samples)})
  df_results = pd.DataFrame(results).dropna()
```
## S&P 500
![stationarity](article_1/trend_stationarity_gspc_t1.png)

# VIX
![stationarity](article_1/trend_stationarity_vix_t1.png)

## EUR
![stationarity](article_1/trend_stationarity_eur_t1.png)

What we're looking for is the solid red line (the median correlation of *T* between the training and test chunks) outside limits of the dotted (-0.20, +0.20) weak significance thresholds. Note that this correlation makes no assumptions about the *direction* of the trend for a given train/test period: *T* is the same whether the security advances in the train period and declines in the test period or advances or declines in both together. None of the charts shows a significant correlation.

## Definition 2
One shortcoming of our trendiness definition is that its numerator is overly sensitive to single-period jumps in price. Consider the case of a security strictly monotonically decreasing in price over the period with the exception of a single jump r<sub>j</sub>.

<div align="center"><img src="article_1/formula_3.png"/></div>
<span hidden>
$$r_j > \sum_{t=0}^{n}r_t \enspace | \enspace t \neq j$$
</span>

then *T > 0*, but would we really care to call this evidence of a trend? Let's try a different definition that addresses this shortcoming:

<div align="center"><img src="article_1/formula_4.png"/></div>

<span hidden>
$$T = 2 * \lvert 0.5 - p(r_t > 0) \rvert $$
</span>

In other words, *T* is the excess probability of non-random price movements within the data in question, and our lambda now becomes:

```
trendiness = lambda chunk: abs(0.5 - np.mean([r > 0 for r in chunk]))
```

## S&P 500
![stationarity](article_1/trend_stationarity_gspc_t2.png)

# VIX
![stationarity](article_1/trend_stationarity_vix_t2.png)

## EUR
![stationarity](article_1/trend_stationarity_eur_t2.png)

Again, we do not find significant correlation in any of the three securities. In fact the correlation coefficient is negative in each case, suggesting that if anything correlation is more likely to appear if it's absent, and disappear if it's present.

## Conclusion
We have looked at two simple models of trendiness. At best they exhibit only weak significance on the studies sampled. There is no clear correlation of trend strength with data window size.

The code can be found [here](trendiness.py).
