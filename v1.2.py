## 初始化函数，设定要操作的股票、基准等等
from jqlib.technical_analysis import *
def initialize(context):
    # 设定指数 沪深300
    g.stockindex = '000300.XSHG' 
    
    g.month = context.current_dt.month
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    #股票池 全局变量
    g.codeList = []
    
    #买入价dict key：code value：买入价
    g.buyPriceDict = {}
    
    #止损dict  key:code value:止损率 默认0.9
    g.cutLostDict = {}
    
    #买入总额dict 如某只股票现在持有总价值
    
    #基本面
    # run_monthly(check_stocks,1,'open')#每年运行一次 需要变动方法内return条件
    run_weekly(check_stocks, 1, time='open')
    #交易函数每天收盘后运行 15:30
    run_daily(trade, time='15:00')   
    
    run_daily(sell, time='every_bar')   
    
## 选股函数（基本面）
def check_stocks(context):
    
    #每年运行一次
    # month = context.current_dt.month
    # if month%12 != g.month%12:
    #     return
    
    # 获取沪深300成分股
    security = get_index_stocks(g.stockindex)
    stocks = get_fundamentals(query(
            valuation.code,# 股票代码
            valuation.pb_ratio, # 市净率
            valuation.circulating_market_cap, # 流通市值
            cash_flow.net_operate_cash_flow,    # 经营活动产生的现金流量净额
        ).filter(
            valuation.code.in_(security),
            valuation.pb_ratio > 1, #市净率>1
            valuation.circulating_market_cap > 200, #流通市值>200亿
            cash_flow.net_operate_cash_flow > 0 #现金流>0 
            
        ))
    
                              
    codes = list(stocks['code']) # 股票代码列表  list类型
    
    
    
    # log.info( codes ) # 输出股票码
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
            # log.info(code,get_security_info(code).display_name,"+++ -2 现金流+++",df_last2.iloc[0,0])
        df_last1 = get_fundamentals(q, statDate = int(context.current_dt.year)-1)
        
        # log.info(df_last1)
        # if not df_last1.empty :
            # log.info(code,get_security_info(code).display_name,"+++ -1 现金流+++",df_last1.iloc[0,0])
        
     
        # df.iloc[0,0] 就是现金流具体数值 iloc[0,0] ，iloc[0,0] 是按照位置获取数据
      
        # start_date = get_security_info(code).start_date #[datetime.date] 类型
        h = attribute_history(code, 1, '1d', ('close')) #历史数据,本行为过去一天的收盘价 
        #  h['close'][0] < 5 or h['close'][0] > 50 or#过滤掉5元以下，50元以上的股票
        if  (not df_last2.empty and df_last2.iloc[0,0] <0) or (not df_last1.empty and df_last1.iloc[0,0]) < 0: # 过滤现金流 < 0 
            codes.remove(code)
        # else:
        #     log.info("~~~~~~~~~~~~~~~",code,get_security_info(code).display_name)
    g.codeList = codes

    log.info( context.current_dt.strftime("%Y-%m-%d"),"基本面选股：",len(g.codeList),"只" ) #列表长度
    # for gCode in g.codeList:
    #     log.info(gCode,get_security_info(gCode).display_name)
    # log.info("******************************")
    return None

##交易函数
def trade(context):
    tradeList = [ ] #交易列表清空
    wantList = [ ] #待购列表
    
    curDate = context.current_dt.strftime("%Y-%m-%d") # 当前逻辑日期 str类型
    for code in g.codeList:
        #指数平均线
        EXPMA34 = EXPMA(code, check_date = curDate, timeperiod=34)[code] 
        EXPMA55 = EXPMA(code, check_date = curDate, timeperiod=55)[code] 
        EXPMA89 = EXPMA(code, check_date = curDate, timeperiod=89)[code] 
        
        #历史数据 过去4天的开盘价 收盘价 成交量（金额）
        h = attribute_history(code, 4, '1d', ('open','close', 'money')) 
        # log.info(h)
        #EXPMA34>EXPMA55>EXPMA89
        #连续三天上涨 (h.iloc[-1]['open']<h.iloc[-1]['close'])
        #成交量增长，三天成交量可以不是递增，但是第2、3天成交量要比第一天上涨大 (h.iloc[-1]['money']>h.iloc[-3]['money'])
        if (EXPMA34>EXPMA55) and (EXPMA55>EXPMA89)and(h.iloc[-4]['open']<h.iloc[-4]['close'])and(h.iloc[-2]['open']<h.iloc[-2]['close'])and(h.iloc[-3]['open']<h.iloc[-3]['close'])and(h.iloc[-2]['money']>h.iloc[-4]['money']): 
            tradeList.append(code) 
        
    log.info("基本面股票池数量：",len(g.codeList))    
    log.info("^^^^^^^^^^^^^可用资金：",context.portfolio.available_cash)
    log.info("####################交易函数选股：",len(tradeList),"只####################" ) 
    for code in tradeList:
        log.info(code,get_security_info(code).display_name)
    log.info("####################交易函数结束####################" ) 
    
                
    # 股票池列表         
    if len(tradeList) > 0 :
        upperband, middleband, lowerband  = Bollinger_Bands(tradeList, check_date = curDate, timeperiod=21, nbdevup=1.5, nbdevdn=1.5)
        for code in tradeList:
            #昨天和今天需要下跌 跌倒MA21之上   ----开盘价 收盘价 MA21 BOLL 成交量
            #1倍标准差
            #并且成交量要小于上涨第三天上涨成交量的75%
            EXPMA21 = EXPMA(code, check_date = curDate, timeperiod=21)[code] 
            
            h_0 = attribute_history(code, 1, '240m', ('open','close', 'money')) #今天的开盘价 收盘价 成交量
            h_1 = attribute_history(code, 2, '1d', ('open','close', 'money'))  #过去两天的。。
            if h_0.iloc[-1]['open']<h_0.iloc[-1]['close'] and h_1.iloc[-1]['open']<h_1.iloc[-1]['close'] and h_0.iloc[-1]['close']>EXPMA21 and upperband[code] > h_0.iloc[-1]['close'] and lowerband[code] < h_0.iloc[-1]['close'] and (h_0.iloc[-1]['money']) < (h_1.iloc[-2]['money']*0.75):
                # log.info("_+_+_+_+_+_+_+",code,h_0.iloc[-1]['money'])
                wantList.append(code) 
                # log.info(code,h_0.iloc[-1]['money'],h_1.iloc[-2]['money'])
       
        
    #买入条件        
    if (len(wantList) > 0 )and (context.portfolio.available_cash>0 ): 
        #交易金额为可用资金的20%
        tradeValue = context.portfolio.available_cash/5/len(wantList)
        for code in wantList:
            order_value(code, tradeValue)
            h_0 = attribute_history(code, 1, '240m', ('close')) #今天收盘价
            g.buyPriceDict[code] = h_0.iloc[-1]['close']
            g.cutLostDict[code] = 0.93
            log.info(code,get_security_info(code).display_name,"买入",tradeValue,"元") 
            
            
#卖出函数        
def sell(context):  
    ## 获取持仓列表
    sell_list = list(context.portfolio.positions.keys())
   
    # 如果有持仓 遍历，卖出条件
    if len(sell_list) > 0 :
        log.info("^^^^^^^^^^^^^",len(sell_list))
        log.info("^^^^^^^^^^^^^可用资金：",context.portfolio.available_cash)
        for sellCode in sell_list:  
            #止损
            h_0 = attribute_history(sellCode, 1, '240m', ('close')) 
           # closePrice = h_0.iloc[-1]['close']#今天收盘价
            buyPrice = g.buyPriceDict[sellCode]#该股票买入价格
            closePrice = get_current_data()[sellCode].last_price
            # cw = str(context.portfolio.positions[sellCode].closeable_amount)
            log.info(sellCode,get_security_info(sellCode).display_name,"现价：【",closePrice,"】 买入价：【",buyPrice,"】 止损率：【"+str(g.cutLostDict[sellCode])+"】 仓位：【"+str(context.portfolio.positions[sellCode].closeable_amount)+"】")
            #止盈30% 条件
            if closePrice >= (buyPrice * 1.3):
                order_target_value(sellCode, 0)
                log.info(sellCode,get_security_info(sellCode).display_name,"止盈清仓") 
            elif closePrice <= buyPrice * g.cutLostDict[sellCode]:
                order_target_value(sellCode, 0)
                log.info(sellCode,get_security_info(sellCode).display_name,"止损清仓") 
            # elif closePrice > (buyPrice) and closePrice <= (buyPrice * 1.1):
            #     log.info(sellCode,get_security_info(sellCode).display_name,"调整止损率为：【",1.03,"】") 
            #     g.cutLostDict[sellCode] = 1.03
            elif closePrice > (buyPrice * 1.1) and closePrice <= (buyPrice * 1.2) and g.cutLostDict[sellCode] != 1.07:
                log.info(sellCode,get_security_info(sellCode).display_name,"调整止损率为：【",1.07,"】") 
                g.cutLostDict[sellCode] = 1.07
            elif closePrice > (buyPrice * 1.2) and closePrice <= (buyPrice * 1.3) and g.cutLostDict[sellCode] != 1.15:
                log.info(sellCode,get_security_info(sellCode).display_name,"调整止损率为：【",1.15,"】") 
                g.cutLostDict[sellCode] = 1.15
            # elif closePrice <= (buyPrice * 0.93) and g.cutLostDict[sellCode] ==0.9 :
            #     order(sellCode, -context.portfolio.positions[sellCode].closeable_amount/2)
            #     log.info(sellCode,get_security_info(sellCode).display_name,"该股票清半仓，且调整止损率为：【",0.87,"】") 
            #     g.cutLostDict[sellCode] = 0.87
                