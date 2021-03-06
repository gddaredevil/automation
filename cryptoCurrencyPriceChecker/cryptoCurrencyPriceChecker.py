#!/usr/bin/python3
import sys
import requests
import time
import logging
import smtplib
import datetime
import os

priceArray = []
prevPrice=[]
cryptoToken = []
prevStr=""

def initiateRequest():
    print("\033[K", end="")
    print("Initiating Request...", end='\r')
    url = "https://api.coindcx.com/exchange/ticker"
    while(1):
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            time.sleep(5)
        #    print(e)
            print("\033[K",end="")
            print("Network Connection Error...",end='\r')
            continue
        #    response=initiateRequest()
        except requests.ConnectionError as r:
            time.sleep(5)
        #    print(e)
            print("\033[K",end="")
            print("Network Connection Error...",end='\r')
            continue
         #   response=initiateRequest()
        data = response.json()
#        print(data)
        return(data)

def getPrice(data, tokens):
    print("\033[K",end="")
    print("Getting Price...",end='\r')
#    print("data: ", data)
    prices=[]
    for token in tokens:
        for i in data:
            if(i['market'].lower()==token.lower()):
                prices.append(float(i['last_price']))
#    print(prices)
    return prices

def validateCurrencies(data, tokens):
    print("\033[K",end="")
    print("Validating Currencies...", end='\r')
    validTokens = []
    found=False
    for token in tokens:
        for i in data:
            if(i['market'].lower()==token.lower()):
                found=True
                validTokens.append(token)
                break
        if(found==False):
            print("Currency {} is Invalid. Please check the spelling once!".format(token))
            print("\nUsage:\n\tYou are supposed to enter in the format Currency_code+buying_currency.\n\tFor e.g.,\n\t\tBitcoin: BTCUSDT/BTCUSDC/BTCINR...\n\t\tEthereum: ETHUSDT/ETHUSDC/ETHINR...")

        found=False
    return(validTokens)


def analyzeData(prices, thresholds, flexMargins):
    print("\033[K",end="")
    print("Analyzing data", end='\r')
    global prevPrice
    global cryptoToken
    global priceArray
    global prevStr
    out = ""
    for i in range(len(prices)):
        if(prices[i]!=prevPrice[i]):
            sys.stdout.write("\033[K")
            if(prices[i] not in priceArray[i]):
                priceArray[i].append(prices[i])
            prevPrice[i] = prices[i]
            for priceVal in reversed(priceArray[i]):
                if(abs((float(prices[i])-float(priceVal))/(prices[i]))*100 >= (thresholds[i]-flexMargins[i]) ):
                    sendMail(cryptoToken[i], priceVal, prices[i])
#                    print(priceArray[i])
                    priceArray[i] = priceArray[i][priceArray[i].index(priceVal)+1:]
#                    print(priceArray[i])
                    break
            out += "{} : {}\t".format(cryptoToken[i],prices[i])
            #Logging
            time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())
            logging.info("\t{} : {} price changed to {}".format(time_str, cryptoToken[i], prices[i]))
        else:
            out += "{} : {}\t".format(cryptoToken[i], prices[i])
    if(out!=prevStr):
        sys.stdout.write("\033[K")
        print(out)
        prevStr=out

def sendMail(currency, prevVal, price):
    print("\033[K", end="")
    print("Sending Mail...", end='\r')
    global cryptoToken
    server = smtplib.SMTP(host='smtp.gmail.com', port=587)
    server.starttls()
    file=open("cred.txt","r") #cred.txt file should contain a dictionary in the format: {'username':'hello@world.com', 'password':'bowchickwowwow'}
    data = file.read()
    cred = eval(data)
    server.login(cred['username'], cred['password'])
    sen=""

    #Logging
    time_str = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime())
    logging.warning("{} : {}".format(time_str, sen))

    if(prevVal > price):
        sen="The value of {} took a dive from {} to {} and decreased by {}% at {}".format(currency, prevVal, price, abs(((prevVal-price)/price)*100) , time_str)
    else:
        sen="The value of {} rose from {} to {} and increased by {}% at {}".format(currency, prevVal, price, abs(((prevVal-price)/price)*100), time_str )
    message="""
    Subject: {} price alert!!

    {}
    """.format(currency, sen)
    server.sendmail(cred['username'], cred['username'], message)
    print(sen)

    

def main():
    global cryptoToken
    global prices
    global prevPrice
    global priceArray

    tokens = input("Enter the Crypto Currency you wanna search: ").split(' ')
    thresholds=[]
    flexMargins=[]
    #print(tokens, len(tokens))
    prevPrice = [0 for i in range(len(tokens))]
    priceArray = [[] for i in range(len(tokens))]
#    print(prevPrice)
#    print(priceArray)
    for i in range(len(tokens)):
        threshold = float(input("Enter the threshold for {}: ".format(tokens[i]))) # You can set the threshold percentage so that any change beyond the set percentage will trigger an email to the mentioned email ID
        #allowedError = float(input("Enter the amount of flexible margin for {}: ".format(tokens[i]))) # You can also set the allowable amount of error in the threshold or can just enter Zero if you are okay with the threshold
        allowedError= (threshold/100.0)*5.0
        thresholds.append(threshold)
        flexMargins.append(allowedError)

    if(os.path.isdir('logs')==False):
        os.system('mkdir logs')

    filename="logs/multiLogFile_"+str(datetime.date.today())+".log"
    logging.basicConfig(filename=filename, level=logging.INFO)

    data = initiateRequest()
    tokens = validateCurrencies(data,tokens)

    if(len(tokens)==0):
        return

    while(True):
        data = initiateRequest()
        cryptoToken = tokens
        prices= getPrice(data, cryptoToken)
        analyzeData(prices, thresholds, flexMargins)
        time.sleep(5)

if __name__=='__main__':
    main() 
