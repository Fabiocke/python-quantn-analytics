from cvm import get_relatorio_cias_abertas_raw, get_relatorio_cias_abertas_infos_raw
from b3apis import get_infos_ativos

import pandas as pd
from functools import lru_cache
from unicodedata import normalize
import re

DICT_TIPOS = {1: 'ITR', 2: 'ITR', 3: 'ITR', 4: 'DFP'}

DICT_RELATORIOS={1:'BPA',
    2:'BPP',
    3:'DRE',
    4:'DRA',
    5:'DMPL',
    6:'DFC_MI',
    7:'DVA'}


INDICADORES = {# Balanço Patrimonial
    'margem ativo circulante' : 'conta(1.01)/conta(1)',
    'margem ativo não circulante' : 'conta(1.02)/conta(1)',
    'capital terceiros' : '(conta(2.01) + conta(2.02))/conta(2)',
    'capital socios' : 'conta(2.03)/conta(2)',
    'passivo oneroso' : '(conta(2.01.04)+conta(2.02.01))/conta(2)',

    # Demonstração de resultado e margens
    'margem bruta' : 'conta(3.03)/conta(3.01)',
    'margem ebit' : 'conta(3.05)/conta(3.01)',
    'margem liquida' : 'conta(3.09)/conta(3.01)',
    'ebitda' : 'conta(3.05) + dsc(6,amortiza ,deprecia)',
    'margem ebitda' : 'ind(ebitda)/conta(3.01)',

    # Demonstração dos fluxos de caixa
    'fco receita' : 'conta(6.01)/conta(3.01)',
    'fci dep' : 'abs(conta(6.02))/dsc(6,amortiza ,deprecia)',
    'fcl' : 'conta(6.01) + conta(6.02)',

    # capital de giro
    'liquidez corrente' : 'conta(1.01)/conta(2.01)',
    'ncg' : '(conta(1.01)-conta(1.01.01)-conta(1.01.02))-(conta(2.01)-conta(2.01.04))',
    'ncg receita' : 'ind(ncg)/conta(3.01)',
    'pmr' : 'conta(1.01.03)/conta(3.01)*360',
    'pme' : 'conta(1.01.04)/abs(conta(3.02))*360',
    'ciclo financeiro' : 'ind(pmr)+ind(pme)-ind(pmp)',

    # endividamento
    'endividamento geral' : 'ind(capital terceiros)',
    'endividamento oneroso' : 'ind(passivo oneroso)',
    'icj' : 'conta(3.05)/abs(conta(3.06))',
    'divida liquida' : '(conta(2.01.04)+conta(2.02.01))-(conta(1.01.01)-conta(1.01.02))',
    #'ebitda' = 'conta(3.05) + conta(6.01.01.03)'
    'alavancamento ebitda' : 'ind(divida liquida)/ind(ebitda)',

    # Analise integrada
    #'margem liquida' = ind
    'giro ativo' : 'conta(3.01)/conta(1)',
    'roa' : 'ind(margem liquida)*ind(giro ativo)',
    'alavancagem pl' : 'conta(1)/conta(2.03)',
    'roe' : 'ind(roa) * ind(alavancagem pl)',
    'roi' : 'conta(3.05)/conta(1)',
    'custo medio divida' : 'abs(conta(3.06))/(conta(2.01)+conta(2.02))'
}


class Relatorio:
    def __init__(self, ano, tri, cod, demonstrativo, acumulado = False, tickers = []):
        self.ano = ano
        self.tri = tri
        self.tipo_periodo = DICT_TIPOS[tri]
        self.cod = self._get_cod(cod)
        self.demonstrativo = demonstrativo
        self.acumulado = acumulado
        self.tickers = tickers
        
    def _get_cod(self, cod):
        return cod if type(cod) == str else DICT_RELATORIOS[cod]  
        
    @lru_cache
    def _get_relatorio(self):
        df = get_relatorio_cias_abertas_raw(self.ano, self.cod, self.tipo_periodo, self.demonstrativo[:3])
        df['CD_CVM'] = df['CD_CVM'].astype(int)
        df['VERSAO'] = df['VERSAO'].astype(int)
        df['VL_CONTA'] = df['VL_CONTA'].astype('float64') 

        df = df[df['ORDEM_EXERC']=='ÚLTIMO']

        for i in df:
            if i.startswith('DT'):
                df[i] = pd.to_datetime(df[i])

        df = df[df['DT_REFER'].dt.month==self.tri * 3]

        if 'DT_INI_EXERC' in df:
            if self.acumulado:
                df=df[df['DT_INI_EXERC']==df.groupby('CD_CVM')['DT_INI_EXERC'].transform('min')]
            else:
                df=df[df['DT_INI_EXERC']==df.groupby('CD_CVM')['DT_INI_EXERC'].transform('max')]

        df = df.drop(['MOEDA', 'ESCALA_MOEDA', 'ORDEM_EXERC', 'ST_CONTA_FIXA'], axis = 1)
        return df
    
    def _get_infos(self):
        df = get_relatorio_cias_abertas_infos_raw(self.ano, self.tipo_periodo)
        df['CD_CVM'] = df['CD_CVM'].astype(int)
        df['VERSAO'] = df['VERSAO'].astype(int)
        for i in df:
            if i.startswith('DT'):
                df[i] = pd.to_datetime(df[i])
        return df
    
    def get_relatorio(self):
        return self._get_relatorio()
    
    def get_infos_relatorio(self):
        return self._get_infos()
    
    def get_infos_ativos(self):
        df = get_infos_ativos()[['codeCVM', 'issuingCompany', 'segment']]\
                .rename(columns = {'codeCVM': 'CD_CVM', 'issuingCompany': 'TICKER', 'segment': 'SEGMENTO'})
        df['CD_CVM'] = df['CD_CVM'].astype(int)
        return df

    def get_infos_relatorio_completo(self):
        df_infos = self.get_infos_relatorio()
        df_ativos = self.get_infos_ativos()
        df = df_infos.merge(df_ativos)
        if self.tickers:
            df = df[df['TICKER'].isin(self.tickers)]
        df = df[df['DT_REFER'].dt.month==self.tri * 3]
        return df

    def get_relatorio_completo(self):
        df = self.get_relatorio()
        df_infos = self.get_infos_relatorio()
        df_ativos = self.get_infos_ativos()
        df = df_infos.merge(df_ativos).merge(df)
        if self.tickers:
            df = df[df['TICKER'].isin(self.tickers)]
        return df
    
    def get_dsc(self, *dscs):
        norm = lambda t: normalize('NFKD', t).encode('ASCII','ignore').decode().lower()
        dscs = map(norm, dscs)
        df = self.get_relatorio_completo()
        return df[[any(i) for i in zip(*[df['DS_CONTA'].apply(norm).str.contains(t).tolist() for t in dscs])]]
    


# classe float para mostrar o tipo de conta
class Conta(float):
    def __new__(self, value, conta, dsc):
        return float.__new__(self, value)
    
    def __init__(self, value, conta, dsc):
        float.__init__(value)
        self.conta = conta
        self.dsc = dsc
        self.num_contas = 1
        
    def __repr__(self):
        return f"conta: {self.conta}\ndescrição: {self.dsc}\nvalor: " + '{:>,.8f}'.format(self.real)
    
    def __check_parentesis(self, dsc, new_sinal):
        sinais = re.findall(r'(?<!\(.)([+\-*/])(?![^()]*\))', dsc)
        
        if new_sinal in ['*', '/'] and '+' in sinais or '-' in sinais:
            dsc = f'({dsc})'
        return dsc
    
    def __operation(self, sinal, other):
        calc = sinal.format(float(other))
        real = eval(str(self.real) + calc)
        new_sinal = sinal[0] 
        
        if isinstance(other, Conta):
            num_contas=self.num_contas+1
            #otherconta = other.conta if other.num_contas==1 else f'({other.conta})'
            #otherdsc = other.dsc if other.num_contas==1 else f'({other.dsc})'
            
            otherconta = other.conta if other.num_contas==1 else self.__check_parentesis(other.conta, new_sinal)
            otherdsc = other.dsc if other.num_contas==1 else self.__check_parentesis(other.dsc, new_sinal)
            
            self.conta = self.__check_parentesis(self.conta, new_sinal)
            conta = self.conta + ' ' + sinal.format(otherconta)
            
            self.dsc = self.__check_parentesis(self.dsc, new_sinal)
            dsc = self.dsc + ' ' + sinal.format(otherdsc)
        elif isinstance(other, float) or isinstance(other, int):
            if other==0:
                return self
            num_contas=self.num_contas+1
            
            self.conta = self.__check_parentesis(self.conta, new_sinal)
            conta = self.conta + ' ' + calc
            
            self.dsc = self.__check_parentesis(self.dsc, new_sinal)
            dsc = self.dsc + ' ' + calc
        else:
            raise ValueError('Formato invalido')
            
        c = Conta(real, conta, dsc)
        c.num_contas=num_contas
        self.old_sinal = sinal[0]
        return c
    
    def __transform(self, sinal):
        c = Conta(eval(sinal.format(self.real)), sinal.format(self.conta), sinal.format(self.dsc))
        return c
            
            
    def __add__(self, other):
        return self.__operation('+ {}', other)
    
    def __radd__(self, other):
        return self.__operation('+ {}', other)


    def __sub__(self, other):
        return self.__operation('- {}', other)
    
    
    def __mul__(self, other):
        return self.__operation('* {}', other)
    
    def __truediv__(self, other):
        return self.__operation('/ {}', other)
    
    def __abs__(self):
        return self.__transform('abs({})')    
    

class AnaliseFundamentalista:
    def __init__(self, ano, tri, tickers, demonstrativo='consolidado', acumulado=False):
        self.ano = ano
        self.tri = tri
        self.tipo_periodo = DICT_TIPOS[tri]
        self.demonstrativo = demonstrativo
        self.acumulado = acumulado
        self.tickers = tickers
        
    def _get_cod(self, cod):
        return cod if type(cod) == str else DICT_RELATORIOS[cod]  
    
    def get_relatorio(self, cod):
        cod = self._get_cod(cod)
        relatorio = Relatorio(self.ano, self.tri, cod, self.demonstrativo, self.acumulado, tickers = self.tickers)
        return relatorio

    def analise_horizontal(self, cod):
        df = self.get_relatorio(cod).get_relatorio_completo()
        df1 = Relatorio(self.ano-1, self.tri, cod, self.demonstrativo, self.acumulado, tickers = self.tickers)\
                .get_relatorio_completo()
        df1=df1.assign(VL_CONTA_ANT = df1['VL_CONTA'])[['CD_CVM', 'CD_CONTA', 'VL_CONTA_ANT']]
        df = df.merge(df1)
        df = df.assign(VARIACAO = lambda x: (x['VL_CONTA']/x['VL_CONTA_ANT']-1).fillna(0))
        return df
    
    def conta(self, *contas):
        df = self.get_relatorio(int(contas[0].split('.')[0])).get_relatorio_completo()
        df = df[df['CD_CONTA'].isin(contas)]
        d = {ticker: sum([Conta(c['VL_CONTA'], c['CD_CONTA'], c['DS_CONTA']) for c in df[df['TICKER'] == ticker].to_dict('records')]) for ticker in df['TICKER'].unique()}
        return d

    
    def dsc(self, cod, *dscs):
        if type(cod)==str and cod.isnumeric():
            cod = int(cod)
        df = self.get_relatorio(cod).get_dsc(*dscs)
        contas=df.groupby('TICKER').CD_CONTA.unique().to_dict()
        scontas = {k:sorted(v, key=len) for k, v in contas.items()}

        
        for k, v in scontas.items():
            contas=[]
            for c in v:
                if not any([c.startswith(i) for i in contas]):
                    contas.append(c)
                scontas[k]=contas
                
        df_contas = pd.DataFrame([[k, i] for k, v in scontas.items() for i in v], columns = ['TICKER', 'CD_CONTA'])    
        df = df.merge(df_contas)
        df = df[['TICKER', 'VL_CONTA', 'CD_CONTA', 'DS_CONTA']]
        d = {ticker: sum([Conta(c['VL_CONTA'], c['CD_CONTA'], c['DS_CONTA']) for c in df[df['TICKER'] == ticker].to_dict('records')]) for ticker in df['TICKER'].unique()}
        return d
    
    
    def ind(self, ind):
        return self.calcular(INDICADORES[ind])
        
    
    def calcular(self, expressao):
        calc = expressao

        inds = [i for i, _ in enumerate(calc) if calc.startswith('ind',i)]
        inds = [calc[i+4: len(calc[:i+4]) + calc[i+4:].find(')')] for i in inds]
        inds = {f'ind({i})':i for i in inds}
        inds = {k:self.ind(v) for k, v in inds.items()}

        contas = [i for i, _ in enumerate(calc) if calc.startswith('conta',i)]
        contas = [calc[i+6: len(calc[:i+6]) + calc[i+6:].find(')')] for i in contas]
        contas = {f'conta({i})':i for i in contas}
        contas = {k:self.conta(v) for k, v in contas.items()}

        dscs = [i for i, _ in enumerate(calc) if calc.startswith('dsc',i)]
        dscs = [calc[i+4: len(calc[:i+4]) + calc[i+4:].find(')')].split(',') for i in dscs]
        dscs = {f'dsc({",".join(i)})':i for i in dscs}
        dscs = {k:self.dsc(*v) for k, v in dscs.items()}

        elements = {**contas, **dscs, **inds}
        l = elements.keys()
        l = [[i, calc.find(i)] for i in l]
        l.sort(key=lambda x: x[1])
        l = [i[0] for i in l]

        contas_ativos = {i:{} for i in set([i for e in elements.values() for i in e.keys()])}
        for k, v in elements.items():
            for i, j in v.items():
                contas_ativos[i].update({k: j})

        contas_ativos = {k:[v.get(i) if v.get(i)!=None else 0 for i in l] for k, v in contas_ativos.items()}

        for n, i in enumerate(l):
            calc = calc.replace(i, f'v[{n}]')
       
        for k, v in contas_ativos.items():
            try:
                contas_ativos[k]=eval(calc)
            except ZeroDivisionError:
                contas_ativos[k]=None
            
        return contas_ativos
    


