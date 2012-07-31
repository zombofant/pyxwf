import re
import email.utils as eutils
from datetime import datetime

def parseHTTPDate(httpDate):
    return datetime(*eutils.parsedate(httpDate)[:6])
    
    
