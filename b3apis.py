import requests
from base64 import b64encode
import pandas as pd
import requests
import warnings
warnings.filterwarnings('ignore')
from functools import lru_cache


def futuros_di():
    r = requests.get('https://cotacao.b3.com.br/mds/api/v1/DerivativeQuotation/DI1')

    infos = [{ 
        **{'symb': i['symb']},
        **{'vcto':i['asset']['AsstSummry']['mtrtyCode']},
        **i['SctyQtn'],
        **{'buyOffer': i['buyOffer']['price'] if 'buyOffer' in i else None},
        **{'sellOffer': i['sellOffer']['price'] if 'sellOffer' in i else None}
        } for i in r.json()['Scty']]

    return infos


def volatilidade_b3(ticker, meses = 12):
    # cria os parâmetros com o trading name
    params = {"language":"pt-br","keyword":ticker,"pageNumber":1,"pageSize":"20"}
    
    # codifica os parâmetros em base64
    params = bytes(str(params), encoding="ascii")
    string = b64encode(params)
    string = string.decode()
    
    r = requests.get('https://sistemaswebb3-listados.b3.com.br/securitiesVolatilityProxy/SecuritiesVolatilityCall/GetListVolatilities/'+string)
    vol = r.json()['results'][0][f'standardDeviation{meses}'].replace(',','.')
    return float(vol)




def encode(string):
    bt = bytes(string, encoding="ascii")
    bt = b64encode(bt).decode()
    return bt

# Função para buscar o trading name
def get_trading_name(ticker):
    # cria os parâmetros
    params = {"language":"pt-br","pageNumber":1,"pageSize":20,"company":ticker}
    string = encode(str(params))
    
    # faz a requisição com os parâmetros
    r = requests.get(r'https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/'+
                         string)
    
    for i in r.json()['results']:
        if i['issuingCompany'].lower() == ticker.lower():
            return i['tradingName'].replace('/','').replace('.','')

    raise ValueError('Empresa não encontrada')
    



def encode(string):
    bt = bytes(string, encoding="ascii")
    bt = b64encode(bt).decode()
    return bt

@lru_cache
def get_infos_ativo(ticker):
    params = {"language":"pt-br","pageNumber":1,"pageSize":100,"company":ticker}
    string = encode(str(params))
    r = requests.get(r'https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/'+
                         string)
    # retorna o trading name da empresa, (é necessário remover pontos e barras)
    for i in r.json()['results']:
        if i['issuingCompany'].lower() == ticker.lower():
            return i



        
@lru_cache
def get_infos_ativo_detalhes(ticker):
    cdcvm = get_infos_ativo(ticker)['codeCVM']
    params = {"codeCVM":cdcvm,"language":"pt-br"}
    string = encode(str(params))

    r = requests.get('https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetDetail/' + string)
    r = r.json()
    return r
        
@lru_cache
def get_infos_ativos(setores = False):
    url = 'https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MCwicGFnZVNpemUiOjEwMDAwfQ=='
    r=requests.get(url, verify=False)
    df=pd.DataFrame(r.json()['results'])
    
    if setores:
        df = df.merge(get_setores(), how='left').drop_duplicates(subset='cnpj')
    return df


@lru_cache
def get_setores():
    setores=requests.get('https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetIndustryClassification/eyJsYW5ndWFnZSI6InB0LWJyIn0=', verify=False).json()
    setores = [[[setor['sector'], s['describle'], i] for s in setor['subSectors'] for i in s['segment']] 
                   for setor in setores]
    setores = [i for j in setores for i in j]
    return pd.DataFrame(setores, columns = ['sector', 'subSector', 'segment'])


# Função para obter os proventos
def get_cash_provents(ticker):
    tradingName = get_infos_ativo(ticker)['tradingName'].replace('/','').replace('.','')
    params = {"language":"pt-br","pageNumber":1,"pageSize":99999,"tradingName":tradingName}
    string = encode(str(params))
    
    r = requests.get('https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/'+
                             string)
    
    return r.json()



def get_market_cap():
    r = requests.get('https://sistemaswebb3-listados.b3.com.br/marketValueProxy/marketValueCall/GetStockExchangeDaily/eyJsYW5ndWFnZSI6InB0LWJyIiwiY29tcGFueSI6IiIsImtleXdvcmQiOiIiLCJwYWdlTnVtYmVyIjoxLCJwYWdlU2l6ZSI6MjB9')
    r = r.json()
    df = pd.DataFrame([[i[j] for j in i if 'Column' in j] for i in r['Body']], 
                columns=[r['Header'][i] for i in r['Header'] if 'Column' in i])
    return df

