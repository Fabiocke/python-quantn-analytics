import numpy as np
from scipy.stats import norm
import pandas as pd

def vol_ewma(serie, lbda = 0.94):
    serie = np.array(serie)
    i = np.arange(len(serie)-1, -1, -1)
    variancia = ((1 - lbda) * lbda ** i * serie ** 2).sum()
    vol = np.sqrt(variancia)
    return vol


def volatilidade(serie, ewma = False):
    return vol_ewma(serie) if ewma else serie.std()


def inv_norm(nc):
    return norm.ppf(nc)


def var_historico(serie, nc):
    return np.quantile(serie, 1 - nc)



def var_parametrico(serie, nc, ewma = False):
    serie = np.array(serie)
    vol = volatilidade(serie, ewma)

    media = serie.mean()
    var = media + vol * norm.ppf(1 - nc)
    return var


def var_parametrico_portfolio(series, pesos, nc, ewma = False):
    pesos = np.array(pesos)
    series = np.array(series)

    medias = np.array([*map(np.mean, series)])
    media_portfolio = (medias * pesos).sum()

    matriz_correl = np.corrcoef(series)

    vols = np.array([*map(lambda x: volatilidade(x, ewma), series)])
    variancia = np.matmul(np.matmul(vols * pesos, matriz_correl), vols * pesos)

    vol_portfolio = np.sqrt(variancia)

    var = media_portfolio + vol_portfolio * norm.ppf(1 - nc)
    return var


def teste_violacao_var(serie, nc, dias = 1, log_retorno = False, ewma = False):
    serie = np.array(serie)
    valores = serie[-dias:]
    retorno_total = valores.sum() if log_retorno else (1 + valores).prod()-1

    var = var_parametrico(serie[:-dias], nc, ewma) * np.sqrt(dias)
    return retorno_total <= var


def backtest(serie, nc, periodo, dias = 1, log_retorno = False, ewma = False):
    testes = pd.Series(serie).rolling(periodo+dias).apply(lambda x: teste_violacao_var(x.tolist(), nc, dias, log_retorno, ewma)).dropna().astype(bool)
    testes = testes.value_counts()
    return {'amostra': testes.sum(),
            'violacoes': testes[True] if True in testes else 0,
            'pct_violacoes': testes[True]/testes.sum() if True in testes else 0}



def beta(rm, ri):
    return np.cov(rm, ri, ddof=0)[0][1] / np.std(rm, ddof=0)**2


def beta_portfolio(rm, retornos, pesos):
    betas = np.array([*map(lambda ri: beta(rm, ri), retornos)])
    return (betas * pesos).sum()

