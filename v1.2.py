## ��ʼ���������趨Ҫ�����Ĺ�Ʊ����׼�ȵ�
from jqlib.technical_analysis import *
def initialize(context):
    # �趨ָ�� ����300
    g.stockindex = '000300.XSHG' 
    
    g.month = context.current_dt.month
    # �趨����300��Ϊ��׼
    set_benchmark('000300.XSHG')
    #��Ʊ�� ȫ�ֱ���
    g.codeList = []
    
    #�����dict key��code value�������
    g.buyPriceDict = {}
    
    #ֹ��dict  key:code value:ֹ���� Ĭ��0.9
    g.cutLostDict = {}
    
    #�����ܶ�dict ��ĳֻ��Ʊ���ڳ����ܼ�ֵ
    
    #������
    # run_monthly(check_stocks,1,'open')#ÿ������һ�� ��Ҫ�䶯������return����
    run_weekly(check_stocks, 1, time='open')
    #���׺���ÿ�����̺����� 15:30
    run_daily(trade, time='15:00')   
    
    run_daily(sell, time='every_bar')   
    
## ѡ�ɺ����������棩
def check_stocks(context):
    
    #ÿ������һ��
    # month = context.current_dt.month
    # if month%12 != g.month%12:
    #     return
    
    # ��ȡ����300�ɷֹ�
    security = get_index_stocks(g.stockindex)
    stocks = get_fundamentals(query(
            valuation.code,# ��Ʊ����
            valuation.pb_ratio, # �о���
            valuation.circulating_market_cap, # ��ͨ��ֵ
            cash_flow.net_operate_cash_flow,    # ��Ӫ��������ֽ���������
        ).filter(
            valuation.code.in_(security),
            valuation.pb_ratio > 1, #�о���>1
            valuation.circulating_market_cap > 200, #��ͨ��ֵ>200��
            cash_flow.net_operate_cash_flow > 0 #�ֽ���>0 
            
        ))
    
                              
    codes = list(stocks['code']) # ��Ʊ�����б�  list����
    
    
    
    # log.info( codes ) # �����Ʊ��
    for code in codes:
        
        q = query(
            cash_flow.net_operate_cash_flow
        ).filter(
            cash_flow.code == code
        )
        # log.info("~~~~~~~~~~~~~~~",code,get_security_info(code).display_name)
      
        df_last2 = get_fundamentals(q, statDate= int(context.current_dt.year)-2)
        # log.info(df_last2)
        # if not df_last2.empty :
            # log.info(code,get_security_info(code).display_name,"+++ -2 �ֽ���+++",df_last2.iloc[0,0])
        df_last1 = get_fundamentals(q, statDate = int(context.current_dt.year)-1)
        
        # log.info(df_last1)
        # if not df_last1.empty :
            # log.info(code,get_security_info(code).display_name,"+++ -1 �ֽ���+++",df_last1.iloc[0,0])
        
     
        # df.iloc[0,0] �����ֽ���������ֵ iloc[0,0] ��iloc[0,0] �ǰ���λ�û�ȡ����
      
        # start_date = get_security_info(code).start_date #[datetime.date] ����
        h = attribute_history(code, 1, '1d', ('close')) #��ʷ����,����Ϊ��ȥһ������̼� 
        #  h['close'][0] < 5 or h['close'][0] > 50 or#���˵�5Ԫ���£�50Ԫ���ϵĹ�Ʊ
        if  (not df_last2.empty and df_last2.iloc[0,0] <0) or (not df_last1.empty and df_last1.iloc[0,0]) < 0: # �����ֽ��� < 0 
            codes.remove(code)
        # else:
        #     log.info("~~~~~~~~~~~~~~~",code,get_security_info(code).display_name)
    g.codeList = codes

    log.info( context.current_dt.strftime("%Y-%m-%d"),"������ѡ�ɣ�",len(g.codeList),"ֻ" ) #�б���
    # for gCode in g.codeList:
    #     log.info(gCode,get_security_info(gCode).display_name)
    # log.info("******************************")
    return None

##���׺���
def trade(context):
    tradeList = [ ] #�����б����
    wantList = [ ] #�����б�
    
    curDate = context.current_dt.strftime("%Y-%m-%d") # ��ǰ�߼����� str����
    for code in g.codeList:
        #ָ��ƽ����
        EXPMA34 = EXPMA(code, check_date = curDate, timeperiod=34)[code] 
        EXPMA55 = EXPMA(code, check_date = curDate, timeperiod=55)[code] 
        EXPMA89 = EXPMA(code, check_date = curDate, timeperiod=89)[code] 
        
        #��ʷ���� ��ȥ4��Ŀ��̼� ���̼� �ɽ�������
        h = attribute_history(code, 4, '1d', ('open','close', 'money')) 
        # log.info(h)
        #EXPMA34>EXPMA55>EXPMA89
        #������������ (h.iloc[-1]['open']<h.iloc[-1]['close'])
        #�ɽ�������������ɽ������Բ��ǵ��������ǵ�2��3��ɽ���Ҫ�ȵ�һ�����Ǵ� (h.iloc[-1]['money']>h.iloc[-3]['money'])
        if (EXPMA34>EXPMA55) and (EXPMA55>EXPMA89)and(h.iloc[-4]['open']<h.iloc[-4]['close'])and(h.iloc[-2]['open']<h.iloc[-2]['close'])and(h.iloc[-3]['open']<h.iloc[-3]['close'])and(h.iloc[-2]['money']>h.iloc[-4]['money']): 
            tradeList.append(code) 
        
    log.info("�������Ʊ��������",len(g.codeList))    
    log.info("^^^^^^^^^^^^^�����ʽ�",context.portfolio.available_cash)
    log.info("####################���׺���ѡ�ɣ�",len(tradeList),"ֻ####################" ) 
    for code in tradeList:
        log.info(code,get_security_info(code).display_name)
    log.info("####################���׺�������####################" ) 
    
                
    # ��Ʊ���б�         
    if len(tradeList) > 0 :
        upperband, middleband, lowerband  = Bollinger_Bands(tradeList, check_date = curDate, timeperiod=21, nbdevup=1.5, nbdevdn=1.5)
        for code in tradeList:
            #����ͽ�����Ҫ�µ� ����MA21֮��   ----���̼� ���̼� MA21 BOLL �ɽ���
            #1����׼��
            #���ҳɽ���ҪС�����ǵ��������ǳɽ�����75%
            EXPMA21 = EXPMA(code, check_date = curDate, timeperiod=21)[code] 
            
            h_0 = attribute_history(code, 1, '240m', ('open','close', 'money')) #����Ŀ��̼� ���̼� �ɽ���
            h_1 = attribute_history(code, 2, '1d', ('open','close', 'money'))  #��ȥ����ġ���
            if h_0.iloc[-1]['open']<h_0.iloc[-1]['close'] and h_1.iloc[-1]['open']<h_1.iloc[-1]['close'] and h_0.iloc[-1]['close']>EXPMA21 and upperband[code] > h_0.iloc[-1]['close'] and lowerband[code] < h_0.iloc[-1]['close'] and (h_0.iloc[-1]['money']) < (h_1.iloc[-2]['money']*0.75):
                # log.info("_+_+_+_+_+_+_+",code,h_0.iloc[-1]['money'])
                wantList.append(code) 
                # log.info(code,h_0.iloc[-1]['money'],h_1.iloc[-2]['money'])
       
        
    #��������        
    if (len(wantList) > 0 )and (context.portfolio.available_cash>0 ): 
        #���׽��Ϊ�����ʽ��20%
        tradeValue = context.portfolio.available_cash/5/len(wantList)
        for code in wantList:
            order_value(code, tradeValue)
            h_0 = attribute_history(code, 1, '240m', ('close')) #�������̼�
            g.buyPriceDict[code] = h_0.iloc[-1]['close']
            g.cutLostDict[code] = 0.93
            log.info(code,get_security_info(code).display_name,"����",tradeValue,"Ԫ") 
            
            
#��������        
def sell(context):  
    ## ��ȡ�ֲ��б�
    sell_list = list(context.portfolio.positions.keys())
   
    # ����гֲ� ��������������
    if len(sell_list) > 0 :
        log.info("^^^^^^^^^^^^^",len(sell_list))
        log.info("^^^^^^^^^^^^^�����ʽ�",context.portfolio.available_cash)
        for sellCode in sell_list:  
            #ֹ��
            h_0 = attribute_history(sellCode, 1, '240m', ('close')) 
           # closePrice = h_0.iloc[-1]['close']#�������̼�
            buyPrice = g.buyPriceDict[sellCode]#�ù�Ʊ����۸�
            closePrice = get_current_data()[sellCode].last_price
            # cw = str(context.portfolio.positions[sellCode].closeable_amount)
            log.info(sellCode,get_security_info(sellCode).display_name,"�ּۣ���",closePrice,"�� ����ۣ���",buyPrice,"�� ֹ���ʣ���"+str(g.cutLostDict[sellCode])+"�� ��λ����"+str(context.portfolio.positions[sellCode].closeable_amount)+"��")
            #ֹӯ30% ����
            if closePrice >= (buyPrice * 1.3):
                order_target_value(sellCode, 0)
                log.info(sellCode,get_security_info(sellCode).display_name,"ֹӯ���") 
            elif closePrice <= buyPrice * g.cutLostDict[sellCode]:
                order_target_value(sellCode, 0)
                log.info(sellCode,get_security_info(sellCode).display_name,"ֹ�����") 
            # elif closePrice > (buyPrice) and closePrice <= (buyPrice * 1.1):
            #     log.info(sellCode,get_security_info(sellCode).display_name,"����ֹ����Ϊ����",1.03,"��") 
            #     g.cutLostDict[sellCode] = 1.03
            elif closePrice > (buyPrice * 1.1) and closePrice <= (buyPrice * 1.2) and g.cutLostDict[sellCode] != 1.07:
                log.info(sellCode,get_security_info(sellCode).display_name,"����ֹ����Ϊ����",1.07,"��") 
                g.cutLostDict[sellCode] = 1.07
            elif closePrice > (buyPrice * 1.2) and closePrice <= (buyPrice * 1.3) and g.cutLostDict[sellCode] != 1.15:
                log.info(sellCode,get_security_info(sellCode).display_name,"����ֹ����Ϊ����",1.15,"��") 
                g.cutLostDict[sellCode] = 1.15
            # elif closePrice <= (buyPrice * 0.93) and g.cutLostDict[sellCode] ==0.9 :
            #     order(sellCode, -context.portfolio.positions[sellCode].closeable_amount/2)
            #     log.info(sellCode,get_security_info(sellCode).display_name,"�ù�Ʊ���֣��ҵ���ֹ����Ϊ����",0.87,"��") 
            #     g.cutLostDict[sellCode] = 0.87
                