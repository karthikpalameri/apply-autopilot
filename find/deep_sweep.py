#!/usr/bin/env python3
"""deep_sweep.py — wide QA/SDET scan over India-startup ATS boards.

Slug sets for boards the 500-company list does not cover. Provider knowledge lives in
`core/ats_boards.py`; the scan+report shape lives in `find/wide_sweep.py`.

Usage: .venv/bin/python find/deep_sweep.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from find.wide_sweep import run

GH = ["hackerrank","toast","freshworks","chargebee","postman","dream11","zoho","zepto","groww","jupiter",
      "meesho","swiggy","moengage","hasura","cred","practo","docusign","mckesson","circana","lightandwonder",
      "n-able","yugabyte","parspec","druva","browserstack","unbxd","clevertap","wingify","contentstack",
      "razorpay","phonepe","flipkart","myntra","netapp","amd","nvidia","oracle","sap","airbnb","stripe",
      "databricks","snowflake","figma","notion","gitlab","hashicorp","elastic","mongodb","confluent",
      "twilio","okta","cloudflare","datadog","sumologic","pagerduty","rubrik","netskope","sophos","sigmoid",
      "thoughtspot","innovaccer","lenskart","nykaa","bigbasket","urbancompany","olas","olacabs","zomato",
      "paytm","bharatpe","sliceit","khatabook","clear","mindtickle","darwinbox","whatfix","locus","zeta",
      "setu","juspay","razorpaysoftware","cashfree","instamojo","pine-labs","signzy","perfios","karza",
      "fampay","jar","sixsigma","navi","kreditbee","moneytap","axio","simpl","epifi","jupiter-money",
      "wysa","curefit","healthifyme","pharmeasy","practo-platform","tata1mg","1mg","medibuddy","niramai",
      "sarvam","krutrim","observe-ai","glance","inmobi","sharechat","dailyhunt","verloop","yellow-ai",
      "haptik","gupshup","kaleyra","tanla","knowlarity","exotel","ozonetel","plivo","chargebee-inc",
      "zolando","swiggy-inc","niku","rippling","retool","vercel","linear","anthropic","openai","deel",
      "remote-com","rippling-inc","gusto","braintree","adyen","checkout-com","plaid","marqeta","brex",
      "ramp","mercury","chime","sofi","affirm","klarna","revolut","wise","nubank","dlocal","payoneer"]
LEV = ["cred","freshworks","chargebee","postman","dream11","zoho","zepto","groww","jupiter","meesho",
       "swiggy","moengage","hasura","practo","khatabook","medibuddy","razorpay","zluri","sprinto",
       "highlevel","kapiva","navi","slice","locus","whatfix","mindtickle","darwinbox","zeta","setu",
       "juspay","cashfree","instamojo","perfios","fampay","jar","epifi","innovaccer","lenskart","nykaa",
       "urbancompany","zomato","paytm","bharatpe","thoughtspot","gainsight","airmeet","hackerearth",
       "interviewbit","scaler","upgrad","unacademy","vedantu","byjus","toppr","doubtnut","classplus",
       "questt","brightchamps","bytelearn","cuemath","simplilearn","greatlearning","edureka"]
ASH = ["postman","chargebee","freshworks","dream11","groww","zepto","jupiter","meesho","swiggy",
       "instawork","khatabook","medibuddy","zluri","sprinto","highlevel","kapiva","navi","slice",
       "locus","whatfix","mindtickle","darwinbox","zeta","setu","juspay","cashfree","perfios","fampay",
       "jar","epifi","innovaccer","thoughtspot","airmeet","hackerearth","scaler","upgrad","unacademy",
       "rippling","retool","vercel","linear","deel","gusto","plaid","marqeta","brex","ramp","mercury",
       "chime","sofi","affirm","klarna","revolut","wise","payoneer","anthropic","openai","observeai",
       "sarvam","krutrim","glance","inmobi","sharechat","verloop","yellowai","haptik"]
SMART = ["Eurofins","PublicisGroupe","Visa","Bosch","Lowe's","Walmart","Deloitte","Accenture","Cognizant",
         "Infosys","Wipro","TCS","Capgemini","Atos","DXC","Fujitsu","NTT","Ericsson","Nokia","Samsung",
         "Siemens","Philips","Honeywell","ABB","Schneider","Caterpillar","Cummins","McKinsey","Bain",
         "Ubisoft","Voodoo","Gameloft","Rakuten","Booking","Expedia","eBay","PayPal","Intuit","Adobe"]
WORKABLE = ["swiggy","meesho","groww","zepto","jupiter","navi","cred","locus","whatfix","mindtickle",
            "darwinbox","zeta","setu","juspay","cashfree","perfios","fampay","jar","epifi","innovaccer",
            "thoughtspot","airmeet","hackerearth","scaler","unacademy","zluri","sprinto","kapiva",
            "highlevel","medibuddy","khatabook","rentomojo","nobroker","housing","magicbricks",
            "lemonade","policybazaar","acko","digit","turtlemint","wheelseye","porter","delhivery",
            "shiprocket","blackbuck","rivigo","vinculum","unicommerce","eshopbox","shipyaari"]
RECRUITEE = ["groww","zepto","jupiter","navi","locus","whatfix","zeta","setu","juspay","cashfree",
             "perfios","fampay","jar","epifi","innovaccer","airmeet","hackerearth","scaler","zluri",
             "sprinto","kapiva","highlevel","medibuddy","khatabook","rentomojo","acko","digit",
             "wheelseye","porter","delhivery","shiprocket","blackbuck","vinculum","unicommerce"]


if __name__ == "__main__":
    run({"greenhouse": GH, "lever": LEV, "ashby": ASH, "smartrecruiters": SMART, "workable": WORKABLE, "recruitee": RECRUITEE})
