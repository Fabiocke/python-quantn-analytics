from analise_fundamentalista import AnaliseFundamentalista
from b3apis import get_infos_ativo_detalhes
from serie_historica import SerieHistorica
from bcb import hist_selic

import pandas as pd

class GeradorFeatures:
    def __init__(self, ano, tri, demonstrativo = 'con', acumulado = False, tickers = []):
        self.ano = ano
        self.tri = tri
        self.demonstrativo = demonstrativo
        self.acumulado = acumulado
        self.tickers = tickers
        self.features_cvm = {}
        
    def set_analise_fundamentalista(self):
        self.af = AnaliseFundamentalista(self.ano, self.tri, demonstrativo = self.demonstrativo, 
                                    acumulado = self.acumulado, tickers=self.tickers) 
        
    def set_analise_fundamentalista_ant(self):
        self.af_ant = AnaliseFundamentalista(self.ano - 1, self.tri, demonstrativo = self.demonstrativo, 
                                    acumulado = self.acumulado, tickers=self.tickers) 
        
        
    def get_code_ativos_b3(self):
        tickers = self.af.get_relatorio(1).get_infos_relatorio_completo()['TICKER'].unique()
        ativos_detalhes = [*map(get_infos_ativo_detalhes, tickers)]
        codes = [i.get('otherCodes') for i in ativos_detalhes]
        codes = [i['code'] for j in codes for i in j]
        return codes
        
    def set_serie_historica(self):
        codes = self.get_code_ativos_b3()
        codes = [code+'.SA' for code in codes if code[4:] in ['3', '4', '11']]
        codes = sorted(codes)
        codes = [code for i, code in enumerate(codes) if code[:4] not in [x[:4] for x in codes[:i]]]
        start = f'{self.ano}-01-01'
        self.sh = SerieHistorica(codes, start = start)
        
        
    def set_df_features(self):
        df = self.af.get_relatorio(1).get_infos_relatorio_completo()
        df = df[['DT_REFER', 'DT_RECEB', 'TICKER', 'SEGMENTO']]
        self.df_features = df
        
    def _get_datas(self, campo = 'DT_RECEB', ant = False):
        obj = self.af if not ant else self.af_ant
        datas = obj.get_relatorio(1).get_infos_relatorio_completo()[['TICKER', campo]]\
            .assign(**{campo: lambda x: x[campo].astype(str)})
        datas = dict(datas.values)
        return datas
        
    def _set_feature_cvm(self, func, params, campo, variacao = False):
        params = params if type(params) in (list, tuple) else [params]
        if campo in self.df_features:
            self.df_features.drop(campo, axis=1, inplace = True)

        res = eval(f'self.af.{func}(*{params})')
        
        if variacao:
            res_ant = eval(f'self.af_ant.{func}(*{params})')
            res = {k: (v / res_ant.get(k) - 1) if res_ant.get(k) else None for k, v in res.items()}
            
        self.features_cvm[campo] = res
        
        df = pd.DataFrame(res.items(), columns = ['TICKER', campo])
        
        df = df[['TICKER', campo]]

        self.df_features = self.df_features.merge(df, how = 'left')
        
     
    def set_conta(self, conta, variacao = False):
        params = conta
        func = 'conta'
        campo = f'conta({params})'
        self._set_feature_cvm(func, params, campo, variacao)
        
    def set_dsc(self, cod, *dscs, variacao = False):
        params = [cod] + list(dscs)
        func = 'dsc'
        campo = f'dsc({",".join(map(str, params))})'
        self._set_feature_cvm(func, params, campo, variacao)
          
    def set_indicador(self, indicador, variacao = False):
        params = indicador
        func = 'ind'
        campo = f'ind({params})'
        self._set_feature_cvm(func, params, campo, variacao)
        
    def set_calculo(self, expressao, variacao = False):
        params = expressao
        func = 'calcular'
        campo = expressao
        self._set_feature_cvm(func, params, campo, variacao)

    def set_selic(self):
        df_selic = hist_selic('anual')
        df_selic = df_selic.reset_index().astype({'data':str})

        datas = self._get_datas('DT_RECEB')
        df_datas = pd.DataFrame(list(datas.items()), columns = ['TICKER', 'data'])

        df = df_datas.merge(df_selic, how='outer')
        df = df.sort_values(by='data')
        df['valor'] = df['valor'].fillna(method = 'ffill')

        df = df.dropna(subset = ['TICKER'])[['TICKER', 'valor']].rename(columns = {'valor': 'tx_selic'})
        self.df_features = self.df_features.merge(df, how = 'left')
        
        
    def set_resultado_hist(self, dias, campo = 'DT_RECEB'):
        datas = self._get_datas(campo)
        res = self.sh.resultado_periodos(datas, dias)
        
        df = pd.DataFrame(list(res.items()), columns = ['TICKER', f'res{dias}'])
        self.df_features = self.df_features.merge(df, how = 'left')
        

        