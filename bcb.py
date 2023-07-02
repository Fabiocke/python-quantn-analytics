import requests
import pandas as pd

def hist_selic(periodo='diario'):
    r=requests.get('https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json').json()
    df = pd.DataFrame(r)
    df['data'] = pd.to_datetime(df['data'], format = '%d/%m/%Y')
    df = df.set_index('data')
    df['valor'] = df['valor'].astype(float)
    if periodo == 'anual':
        df['valor'] = df['valor'].apply(lambda x: 1+x/100)**252-1
    return df

def selic(periodo='diario', data=None):
    selic=hist_selic(periodo)
    if data:
        selic=selic['valor'][data]
    else:
        selic=selic['valor'].iloc[-1]
    return selic

