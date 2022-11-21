import numpy as np
from b3apis import get_infos_ativos, get_market_cap

def net_gross(nets, cash = 0):
    nets = np.array(nets)
    total = nets.sum() + cash
    long = nets[nets>0].sum()/total
    short = nets[nets<0].sum()/total
    net_gross = {'net': long+short, 'gross': long-short}
    return net_gross


def exposure_weights(nets, cash = 0):
    nets = np.array(nets)
    total = nets.sum() + cash
    return np.array(nets)/total


def exposure_long_short(nets, cash = 0):
    nets = np.array(nets)
    total = nets.sum() + cash
    long = nets[nets>0].sum()/total
    short = nets[nets<0].sum()/total
    return {'long':long, 'short':short}


def get_company_infos(tickers, sectors = False):
    tickers = [ticker[:4] for ticker in tickers]
    infos = get_infos_ativos(sectors)
    return infos[infos['issuingCompany'].isin(list(tickers))]


def get_net_gross_by_sector(tickers, nets):
    tickers = [ticker[:4] for ticker in tickers]
    infos = get_company_infos(tickers, True)
    infos = infos[['issuingCompany', 'sector']]
    infos['net'] = infos['issuingCompany'].replace(dict(zip(tickers, nets)))
    net_gross_by_sector = infos.groupby('sector').apply(lambda x: net_gross(x['net'].values)).to_dict()
    return net_gross_by_sector


def get_exposure_long_short_by_sector(tickers, nets):
    tickers = [ticker[:4] for ticker in tickers]
    infos = get_company_infos(tickers, True)
    infos = infos[['issuingCompany', 'sector']]
    infos['net'] = infos['issuingCompany'].replace(dict(zip(tickers, nets)))
    long_short_by_sector = infos.groupby('sector').apply(lambda x: exposure_long_short(x['net'].values)).to_dict()
    return long_short_by_sector

    

def get_exposure_by_range_market_cap():
    mcap = get_market_cap()

    mcap = mcap[['Empresa', 'R$ (Mil)']]
    mcap.columns = ['tradingName', 'market_cap']

    infos = self.get_infos()










'''
        
d = {'VALE3': 10000,
    'CVCB3': 9300,
    'TOTS3': 8000,
    'COGN3': 8300,
    'SUZB3': 2300,
    'LREN3': -5000,
    'RENT3': -3500,
    'CYRE3': -2300,
    'USIM5': -1100}

nets = [10000, 9300, 8000, 8300, 2300, -5000, -3500, -2300, -1100]

tickers = ['VALE3', 'CVCB3', 'TOTS3', 'COGN3', 'SUZB3', 'LREN3', 'RENT3', 'CYRE3', 'USIM5']

'''



