import webapp2, os, json, jinja2, logging, urllib, urllib2
from Crypto.Hash import keccak

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                                                           extensions=['jinja2.ext.autoescape'], autoescape=True)

class GreetHandler(webapp2.RequestHandler):
    def get(self):
        jinjadict={"page_title":"Check Your Password"}
        template =JINJA_ENVIRONMENT.get_template('projectform.html')
        self.response.write(template.render(jinjadict))

class GreetResponseHandler(webapp2.RequestHandler):
    def post(self):
        password = self.request.get('password')
        go = self.request.get('gobtn')
        if password:
            # if form filled in, tell if their password is safe
            passwordinfo = safeTestPassword(password)
            if type(passwordinfo) is dict: #if password is in api, aka it is not safe
                breachcount = passwordinfo['SearchPassAnon']['count']
                digits = passwordinfo['SearchPassAnon']['char']['D']
                letters = passwordinfo['SearchPassAnon']['char']['A']
                special = passwordinfo['SearchPassAnon']['char']['S']
                length = passwordinfo['SearchPassAnon']['char']['L']
                jinjadict = {"page_title": "Unsafe Password", "breachcount": breachcount, "digits":digits,
                             "alphabet": letters, "special": special, "length": length}
                template = JINJA_ENVIRONMENT.get_template('badprojectresponse.html')
            else: #if password is safe
                logging.info(password)
                jinjadict = {"page_title": "Safe Password"}
                template = JINJA_ENVIRONMENT.get_template('projectresponse.html')
            self.response.write(template.render(jinjadict))
        else:
            #if not, then show the form again with a correction to the user
            jinjadict = {'prompt':"Sorry, I will need you to enter a password for me to check."}
            template = JINJA_ENVIRONMENT.get_template('projectform.html')
            self.response.write(template.render(jinjadict))

### Utility functions you may want to use
def safeGet(url):
    try:
        return urllib2.urlopen(url)
    except urllib.error.HTTPError as e:
        logging.error("The server couldn't fulfill the request.")
        logging.error("Error code: ", e.code)
    except urllib.error.URLError as e:
        logging.error("We failed to reach a server")
        logging.error("Reason: ", e.reason)
    return None

def testPassword(password):
    baseurl = 'https://passwords.xposedornot.com/api/v1/pass/anon/'
    password = password.encode()
    keccak_hash = keccak.new(digest_bits=512)
    keccak_hash.update(password)
    newstr = keccak_hash.hexdigest()[:10]
    url = baseurl + newstr

    # add a user agent that pretends to be a browser - code credit to Prof. Munson :)
    xposedreq = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    )

    xposed = urllib.request.urlopen(xposedreq)
    requeststr = xposed.read()
    data = json.loads(requeststr)
    return data

def safeTestPassword(password):
    try:
       return testPassword(password)
    except urllib.error.HTTPError as error:
        if hasattr(error, "code"):
            if error.code == 404:
                return("Looks like your password is safe, it isn't in our database of breached passwords!")
            else:
                return("Error: %s" % error)
        else:
            return("Error: %s" % error)
# Tester Code
print(safeTestPassword("123456"))

application = webapp2.WSGIApplication([('/', GreetHandler), ('/gresponse', GreetResponseHandler)], debug=True)
