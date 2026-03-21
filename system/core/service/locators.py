'''
Seletores do Yahoo News e padrões regex pra extração de dados.
Tudo centralizado aqui pra facilitar manutenção.
'''


class YahooNewsLocators:
    '''
    Seletores XPath pro Yahoo News.
    filtrei pelo bloco (retirando os anúncios) e coletando elementos unicos 
    para capturar os dados necessarios abaixo
    '''

    # bloco da noticia completa (filtre por essa classe para nao coletar anuncios)
    ITEM_NOTICIA = "//li[contains(@class,'js-stream-content')]"

    # filtro do bloco noticia para pegar cada item unico, dos elementos abaixo
    TITULO = ".//h3[contains(@class,'stream-item-title')]"
    RESUMO = ".//p[contains(@class,'Fz')]"
    TEMA = ".//div[contains(@class,'Mb(4px)')]//strong"
    FONTE = ".//div[contains(@class,'Mb(4px)')]//span[contains(@class,'Ell')]"
    TEMPO_LEITURA = ".//div[contains(@class,'Ai(c)')]//span"

    LIMITE = 5

