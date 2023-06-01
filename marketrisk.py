import numpy as np
from scipy.stats import norm
import pandas as pd


def var_historico(serie, nc):
    return np.quantile(serie, 1 - nc)


# função para calcular a volatildiade ewma
def vol_ewma(serie, lbda = 0.94):
    # gera uma lista decrescente do número total de elementos menos um até 0
    i = np.arange(len(serie)-1, -1, -1)
    
    # aplicação da formula para gerar a variância
    variancia = ((1 - lbda) * lbda ** i * serie ** 2).sum()
    
    # calcula a raiz da variância 
    vol = np.sqrt(variancia)
    return vol

def vol_portfolio(series, volumes, ewma = False):
    pesos = np.array(volumes) / sum(volumes)
    matriz_correl = np.corrcoef(series)
    vols = np.array([vol_ewma(x) if ewma else x.std() for x in series])
    variancia = np.matmul(np.matmul(vols * pesos, matriz_correl), vols * pesos)
    vol = np.sqrt(variancia)
    return vol

from scipy.stats import norm

# media = media dos retornos
# nc = nível de confiança
# vol = Volatilidade
# dias = horizonte de tempo
# volume = volume financeiro do portfolio ou ativo
def calc_var_parametrico(media, nc, vol, volume, dias):
    var = (media - norm.ppf(nc) * vol * np.sqrt(dias)) * volume
    return var

# calculo do var para um portfolio
def var_parametrico_portfolio(series, volumes, nc, dias, ewma = False):
    # calcula o volume total
    volume_total = sum(volumes)
    
    # Calcula as médias de cada ativo
    medias = [np.mean(serie) for serie in series]
    
    # Calcula a soma ponderada das médias
    pesos = np.array(volumes) / volume_total
    media_portfolio = (medias * pesos).sum()
    
    # calcula a volatilidade do portfolio
    vol = vol_portfolio(series, volumes, ewma)
    
    # calcula o var
    var = calc_var_parametrico(media_portfolio, nc, vol, volume_total, dias)
    return var

def teste_violacao_var(series, volumes, nc, dias, ewma):
    # Calcula os pesos
    pesos = np.array(volumes) / sum(volumes)

    # Subtrai os dias de teste para gerar as séries usadas no calculo do VaR
    series_calculo = series[:, :-dias]

    # Calcula o resultado dos dias de teste
    resultado_ativo = [(1 + serie).prod() - 1 for serie in series[:, -dias:]]
    resultado_total = (resultado_ativo * pesos).sum() * sum(volumes)

    # Calcula o VaR
    var = var_parametrico_portfolio(series_calculo, volumes, nc, dias, ewma)

    # Verifica se o resultado é uma perda maior que o VaR
    return resultado_total <= var

# periodo: um número inteiro que representa o número de dias para 
#          cada período no qual o teste de backtesting é realizado.
# dias: representa o número de dias que o VaR será testado.
def backtesting(series, volumes, nc, periodo, dias, ewma = False):
    # Divide as séries em períodos com a quantidade de dias indicado
    list_series = [series[:, i: i + periodo + dias] for i in range(len(df) - periodo - dias)]

    # Gera os testes
    testes = [teste_violacao_var(series, volumes, nc, dias, ewma) for series in list_series]

    # Cria um dicionário com a quantidade de resultados positivos e negativos
    resultados = dict(zip(*np.unique(testes, return_counts=True)))

    # Verifica a quantidade de violações
    violacoes = resultados.get(True) or 0

    # Calcula a porcentagem de violações
    pct_violacoes = (resultados.get(True) or 0) / len(testes) 

    return {'amostra': len(testes),
            'violacoes': resultados.get(True) or 0,
            'pct_violacoes': (resultados.get(True) or 0) / len(testes)}



def beta(rm, ri):
    return np.cov(rm, ri, ddof=0)[0][1] / np.std(rm, ddof=0)**2


def beta_portfolio(rm, retornos, pesos):
    betas = np.array([*map(lambda ri: beta(rm, ri), retornos)])
    return (betas * pesos).sum()


def gerar_composicao_carteira(series, rf, seed = None):
    np.random.seed(seed)
    pesos = np.random.random(len(series))
    pesos = pesos/pesos.sum()
    
    medias = np.array([*map(np.mean, series)])

    retorno = (pesos * medias).sum()
    vol = vol_portfolio(series, pesos)
    
    sharpe_ratio = (r - rf) / vol
    
    return pesos, retorno, vol, sharpe_ratio
    

def markovits(series, rf, qtd):
    carteiras=[gerar_composicao_carteira(series, rf) for i in range(qtd)]

    df = pd.DataFrame(carteiras, columns = ['peso', 'retorno', 'volatilidade', 'sharpe_ratio'])
    df = df.sort_values(by='sharpe_ratio', ascending=False)
    return df


