import yfinance as yf

class SerieHistorica:
    def __init__(self, tickers, start, end = None):
        #tickers = [e for i, e in enumerate(sorted(tickers)) if e[:4] 
        #                         not in [item[:4] for item in tickers[:i]]]
        self.tickers = tickers
        self.start = start
        self.end = end
        self._set_series()
        

    def _set_series(self):
        df = yf.download(self.tickers, start = self.start, end = self.end)
        self.df = df
    
    def resultado_periodos(self, datas, dias):
        df = self.df['Adj Close'].dropna(axis=1)
        tickers = list(df)
        df = df[[e for i, e in enumerate(sorted(tickers)) if e[:4] 
                                 not in [item[:4] for item in tickers[:i]]]]
        df = df.rename(columns = {i: i[:4] for i in df})
        res = df.shift(-dias)[:-dias] / df[:-dias] - 1
        return {k: res[res.index.astype(str).str[:10] > v][k].iloc[0] for k, v in datas.items()}

        