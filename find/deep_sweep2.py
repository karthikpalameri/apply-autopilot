#!/usr/bin/env python3
"""deep_sweep2.py — wide QA/SDET scan over India-origin product boards (devtools/AI/fintech).

Curated slug sets for boards the 500-company list does not cover. Provider knowledge lives
in `core/ats_boards.py`; the scan+report shape lives in `find/wide_sweep.py`.

Usage: .venv/bin/python find/deep_sweep2.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from find.wide_sweep import run

GH = [
 # devtools / infra
 "sentry","postman-inc","kong","grafana","temporal","cockroachlabs","planetscale","supabase","neon",
 "clickhouse","timescale","redis","couchbase","neo4j","scylla","dragonfly","redpanda","starburst",
 "dbtlabs","fivetran","airbyte","astronomer","prefect","dagster","dagster-labs","dagsterlabs",
 "harness","spinnaker","jfrog","sonarsource","snyk","semgrep","veracode","checkmarx","contrast",
 "lacework","wiz","orca-security","cyera","vanta","drata","secureframe","teleport","tailscale",
 # ai / ml
 "scaleai","scale-ai","huggingface","weightsandbiases","wandb","determined-ai","anyscale","modal",
 "together","together-ai","perplexity","cohere","mistral","pinecone","weaviate","qdrant","chroma",
 "langchain","llamaindex","zilliz","deepgram","assemblyai","elevenlabs","runway","stability",
 # global product cos w/ India hubs
 "atlassian","asana","airtable","miro","coda","loom","calendly","zapier","make","n8n","retool-inc",
 "amplitude","mixpanel","heap","segment","braze","iterable","klaviyo","customer-io","sendgrid",
 "coupa","zendesk","freshworks-inc","intercom","drift","gong","clari","outreach","salesloft","apollo",
 "zoom","twilio-inc","vonage","talkdesk","ringcentral","genesys","nice","five9","8x8","dialpad",
 "box","dropbox","egnyte","sharefile","smartsheet","monday","clickup","notion-labs","obsidian",
 "canva","adobe","autodesk","bentley","ptc","ansys","dassault","siemens-digital","hexagon",
 # fintech / payments (global w/ India)
 "adyen-inc","worldpay","fiserv","fis","jackhenry","ncr","diebold","deluxe","q2","nCino","tememos",
 "blend","better","rocket","quickenloans","zillow","redfin","compass","opendoor","oscar","clover",
 "fiserv-inc","global-payments","nuvei","paysafe","neteller","skrill","checkout","rapyd","dlocal-inc",
 "tipalti","bill","avidxchange","coupa-software","procore","buildertrend","servicetitan","jobber",
 # health / bio
 "tempus","flatiron","veracyte","guardant","natera","exact-sciences","illumina-inc","pacbio",
 "10xgenomics","recursion","insitro","atomwise","benchling","sciencedirect","elsevier","clarivate",
 "iqvia","viatris","cigna","elevance","humana","unitedhealth","anthem","centene","mckesson-inc",
 "cardinalhealth","henryschein","zocdoc","doximity","teladoc","amwell","hims","ro","hinjah",
 # india-origin product cos
 "zerodha","smallcase","tickertape","upstox","angelone","angel-one","5paisa","dhan","groww-inc",
 "coinswitch","wazirx","coindcx","mudrex","vauld","pillow","spenny","jupiter-money-inc","atome",
 "khatabook-inc","okcredit","vyapar","zoho-inc","keka-hr","darwinbox-inc","peoplebox","leoforce",
 "nirvana","matrice","thence","kalido","spotdraft","dhiwise","deepsource","codemagic","appsmith",
 "tooljet","rows","rowy","ilert","signoz","last9","netra","observe-inc","atsign","techjini",
 "happiest-minds","innovaccer-inc","healthify","cultfit","curefit-inc","darwinbox-hr","wysa-inc",
 "suki","augmedix","qventus","wellthy","curai","khealth","infermedica","aidoc","viz-ai",
]
LEV = ["mindtickle","innovaccer","whatfix","locus","zeta","setu","juspay","cashfree","perfios",
       "fampay","jar","epifi","sharechat","verloop","yellowai","haptik","gupshup","kaleyra",
       "airmeet","hackerearth","scaler","upgrad","unacademy","vedantu","classplus","brightchamps",
       "leoforce","spotdraft","deepsource","appsmith","tooljet","signoz","last9","rentomojo",
       "acko","digit","wheelseye","porter","delhivery","shiprocket","blackbuck","vinculum",
       "unicommerce","eshopbox","nobroker","magicbricks","housing","policybazaar","turtlemint",
       "khatabook","okcredit","vyapar","coinswitch","smallcase","tickertape","zerodha","upstox",
       "capillary","capillarytech","moengage-inc","clevertap-inc","wingify-inc","vwo","browserstack-inc",
       "lambdaTest","lambdatest","testsigma","testrig","qa-mentor","pahamify","toppr","doubtnut",
       "byjus","unacademy-inc","simplilearn","greatlearning","edureka","niramai","dozee","healthplix",
       "practo-inc","pharmeasy-inc","1mg-inc","truemeds","netmeds","apollo-247","medibuddy-inc"]
ASH = ["sentry","postman","grafana","temporal","clickhouse","supabase","neon","redis","couchbase",
       "harness","snyk","wiz","vanta","tailscale","scaleai","huggingface","weightsandbiases",
       "anyscale","modal","perplexity","cohere","pinecone","weaviate","qdrant","langchain",
       "deepgram","elevenlabs","runway","atlassian","asana","airtable","miro","loom","calendly",
       "zapier","retool","amplitude","mixpanel","braze","klaviyo","intercom","gong","clari",
       "zoom","talkdesk","box","dropbox","smartsheet","notion","canva","figma-inc","adyen",
       "checkout","tipalti","procore","servicetitan","tempus","benchling","zocdoc","teladoc",
       "zerodha","smallcase","coinswitch","spotdraft","deepsource","appsmith","tooljet","signoz",
       "last9","innovaccer","whatfix","locus","zeta","setu","juspay","cashfree","perfios",
       "fampay","jar","epifi","sharechat","verloop","haptik","gupshup","airmeet","hackerearth",
       "scaler","leoforce","rentomojo","acko","digit","wheelseye","porter","delhivery",
       "shiprocket","blackbuck","vinculum","unicommerce","nobroker","policybazaar","turtlemint",
       "capillary","moengage","clevertap","wingify","browserstack","lambdatest","testsigma"]
SMART = ["Freshworks","Chargebee","Zoho","BrowserStack","HackerRank","LambdaTest","Testsigma",
         "Icertis","Zycus","Mindtree","LTIMindtree","Persistent","Mphasis","Hexaware","Birlasoft",
         "Zensar","Coforge","HappiestMinds","Subex","Tanla","RouteMobile","Datamatics","Sasken",
         "Sonata","InfosysBPM","TechMahindra","Virtusa","Xebia","Thoughtworks","EPAM","Globant",
         "Encora","Nagarro","PublicisSapient","Grid","Vodafone","Telefonica","Orange","BT",
         "StandardChartered","HSBC","Barclays","DeutscheBank","UBS","Citi","JPMorgan","GoldmanSachs",
         "MorganStanley","BNY","StateStreet","NorthernTrust","Fidelity","Schroders","Invesco"]


if __name__ == "__main__":
    run({"greenhouse": GH, "lever": LEV, "ashby": ASH, "smartrecruiters": SMART})
