import requests, io, requests
from zipfile import ZipFile
import pandas as pd
from functools import lru_cache


@lru_cache
def get_relatorio_cias_abertas_raw(ano, cod, tipo_periodo, demonstrativo):
    url=f'http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{tipo_periodo}/DADOS/{tipo_periodo.lower()}_cia_aberta_{ano}.zip'
    file = f'{tipo_periodo.lower()}_cia_aberta_{cod}_{demonstrativo}_{ano}.csv'
    r=requests.get(url)
    zf = ZipFile(io.BytesIO(r.content))
    file = zf.open(file)
    df = pd.read_csv(file, encoding = 'ISO-8859-1', sep = ';')
    return df

@lru_cache
def get_relatorio_cias_abertas_infos_raw(ano, tipo_periodo):
    url=f'http://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{tipo_periodo}/DADOS/{tipo_periodo.lower()}_cia_aberta_{ano}.zip'
    file = f'{tipo_periodo.lower()}_cia_aberta_{ano}.csv'
    r=requests.get(url)
    zf = ZipFile(io.BytesIO(r.content))
    file = zf.open(file)
    df = pd.read_csv(file, encoding = 'ISO-8859-1', sep = ';')
    return df

