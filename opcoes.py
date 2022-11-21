from scipy.stats import norm
import numpy as np
import requests
import pandas as pd

# Obtem os vencimentos
def vencimentos(ticker):
    url = f'https://opcoes.net.br/listaopcoes/completa?au=False&uinhc=0&idLista=ML&idAcao={ticker}&listarVencimentos=true&cotacoes=true'
    response = requests.get(url, verify=False).json()
    vctos = [[i['value'], i['text']] for i in response['data']['vencimentos']]
    return vctos

# Obtem as opções
def listar_opcoes(ticker):
    # Busca os vencimentos
    vctos = vencimentos(ticker)
    opcs=[]
    
    # Busca as opções para cada data de vencimento
    for vcto in vctos:
        url=f'https://opcoes.net.br/listaopcoes/completa?au=False&uinhc=0&idLista=ML&idAcao={ticker}&listarVencimentos=false&cotacoes=true&vencimentos={vcto[0]}'
        response = requests.get(url).json()
        
        # Busca apenas os campos necessários
        opcs += ([[ticker]+[i[0][:i[0].find('_')]] + i[2:4] + [vcto[1]] + [i[5]] + [i[8]] for i in response['data']['cotacoesOpcoes']])
    
    # Gera o dataframe
    colunas = ['ATIVO_OBJ','ATIVO', 'TIPO', 'MOD', 'DT_VCTO', 'STRIKE', 'PRECO']
    opcs = pd.DataFrame(opcs, columns=colunas)
    
    # transforma o campo vencimento e datetime
    opcs['DT_VCTO'] = pd.to_datetime(opcs['DT_VCTO'])
    
    return opcs


def d1(S, K, r, sigma, T):
    return (np.log(S/K) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))

def d2(S, K, r, sigma, T):
    return (np.log(S/K) + (r - sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))

def bsm_call(S, K, r, sigma, T):
    return (S * norm.cdf(d1(S, K, r, sigma, T)) - (K * np.exp(-r * T) * norm.cdf(d2(S, K, r, sigma, T))))

def bsm_put(S, K, r, sigma, T):
    return  - (S * norm.cdf(-d1(S, K, r, sigma, T))) + (K * np.exp(-r * T) * norm.cdf(-d2(S, K, r, sigma, T)))




def vol_implicita(P, S, K, r, T, func):
    sigma = 5
    while True:
        dif = func(S, K, r, sigma, T)/P-1
        if abs(dif) < 0.001:
            return sigma
        elif dif > 0:
            sigma -= (sigma/2)
        else:
            sigma += (sigma/2)
            
            
def vol_implicita_call(P, S, K, r, T):
    return vol_implicita(P, S, K, r, T, bsm_call)
    
def vol_implicita_put(P, S, K, r, T):
    return vol_implicita(P, S, K, r, T, bsm_put)


