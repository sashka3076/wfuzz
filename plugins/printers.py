import socket
import json as jjson
from xml.dom import minidom

from framework.externals.moduleman.plugin import moduleman_plugin
from framework.plugins.base import BasePrinter

@moduleman_plugin("header", "footer", "result")
class magictree(BasePrinter):
    name = "magictree"
    description = "Prints results in magictree format"
    category = ["default"]
    priority = 99

    def __init__(self, output):
        BasePrinter.__init__(self, output)
	self.node_mt = None
	self.node_service = None

    def __create_xml_element(self, parent, caption, text):
	# Create a <xxx> element
	doc = minidom.Document()
	el = doc.createElement(caption)
	parent.appendChild(el)

	# Give the <xxx> element some text
	ptext = doc.createTextNode(text)

	el.appendChild(ptext)
	return el

    def header(self, summary):
	doc = minidom.Document()

	#<magictree class="MtBranchObject">
	self.node_mt = doc.createElement("magictree")
	self.node_mt.setAttribute("class", "MtBranchObject")

	#<testdata class="MtBranchObject">
	node_td = doc.createElement("testdata")
	node_td.setAttribute("class", "MtBranchObject")
	self.node_mt.appendChild(node_td)

	#<host>209.85.146.105
	host = summary.seed.history.host
	if host.find(":") > 0:
	    host, port = host.split(":")
	else:
	    port = 80
	    if summary.seed.history.scheme.lower() == "https":
		port = 443

	try:
	    resolving = socket.gethostbyname(host)
	    node_h = self.__create_xml_element(node_td, "host", str(resolving))
	except socket.gaierror:
	    node_h = self.__create_xml_element(node_td, "host", str(host))

	#<ipproto>tcp
	node_ipr = self.__create_xml_element(node_h, "ipproto", "tcp")

	#<port>80<state>open</state><service>http
	node_port = self.__create_xml_element(node_ipr, "port", str(port))
	self.__create_xml_element(node_port, "state", "open")
	if summary.seed.history.scheme.lower() == "https":
	    node_port = self.__create_xml_element(node_port, "tunnel", "ssl")

	self.node_service = self.__create_xml_element(node_port, "service", "http")

    def result(self, fuzz_result):
	node_url = self.__create_xml_element(self.node_service, "url", str(fuzz_result.url))

	if 'Server' in fuzz_result.history.headers.response:
	    self.__create_xml_element(node_url, "HTTPServer", fuzz_result.history.headers.response['Server'])

	location = ""
	if 'Location' in fuzz_result.history.headers.response:
	    location = fuzz_result.history.headers.response['Location']

	if fuzz_result.code == 301 or fuzz_result.code == 302 and location:
	    self.__create_xml_element(node_url, "RedirectLocation", location)

	self.__create_xml_element(node_url, "ResponseCode", str(fuzz_result.code))
	self.__create_xml_element(node_url, "source", "WFuzz")

    def footer(self, summary):
	self.f.write(self.node_mt.toxml())

@moduleman_plugin("header", "footer", "result")
class html(BasePrinter):
    name = "html"
    description = "Prints results in html format"
    category = ["default"]
    priority = 99

    def __init__(self, output):
        BasePrinter.__init__(self, output)

    def header(self, summary):
	url = summary.url

	self.f.write("<html><head></head><body bgcolor=#000000 text=#FFFFFF><h1>Fuzzing %s</h1>\r\n<table border=\"1\">\r\n<tr><td>#request</td><td>Code</td><td>#lines</td><td>#words</td><td>Url</td></tr>\r\n" % (url) )

    def result(self, fuzz_result):
	htmlc="<font>"

	if fuzz_result.code >= 400 and fuzz_result.code < 500:
	    htmlc = "<font color=#FF0000>"
	elif fuzz_result.code>=300 and fuzz_result.code < 400:
	    htmlc = "<font color=#8888FF>"
	elif fuzz_result.code>=200 and fuzz_result.code < 300:
	    htmlc = "<font color=#00aa00>"

	if fuzz_result.history.method.lower() == "post":
	    inputs=""
	    for n, v in fuzz_result.history.parameters.post.items():
		inputs+="<input type=\"hidden\" name=\"%s\" value=\"%s\">" % (n, v)

	    self.f.write ("\r\n<tr><td>%05d</td>\r\n<td>%s%d</font></td>\r\n<td>%4dL</td>\r\n<td>%5dW</td>\r\n<td><table><tr><td>%s</td><td><form method=\"post\" action=\"%s\">%s<input type=submit name=b value=\"send POST\"></form></td></tr></table></td>\r\n</tr>\r\n" %(fuzz_result.nres, htmlc, fuzz_result.code, fuzz_result.lines, fuzz_result.words, fuzz_result.description, fuzz_result.url, inputs))
	else:
	    self.f.write("\r\n<tr><td>%05d</td><td>%s%d</font></td><td>%4dL</td><td>%5dW</td><td><a href=%s>%s</a></td></tr>\r\n" %(fuzz_result.nres, htmlc, fuzz_result.code, fuzz_result.lines, fuzz_result.words, fuzz_result.url, fuzz_result.url))

    def footer(self, summary):
	self.f.write("</table></body></html><h5>Wfuzz by EdgeSecurity<h5>\r\n")

@moduleman_plugin("header", "footer", "result")
class json(BasePrinter):
    name = "json"
    description = "Results in json format"
    category = ["default"]
    priority = 99


    def __init__(self, output):
        BasePrinter.__init__(self, output)
        self.json_res = []

    def header(self, res):
        pass

    def result(self, res):
	server = ""
	if 'Server' in res.history.headers.response:
	    server = res.history.headers.response['Server']
	location = ""
	if 'Location' in res.history.headers.response:
	    location = res.history.headers.response['Location']
	elif res.history.url != res.history.redirect_url:
	    location = "(*) %s" % res.history.url
        post_data = {}
	if res.history.method.lower() == "post":
	    for n, v in res.history.parameters.post.items():
                post_data[n] = v

        res_entry = {"lines": res.lines, "words": res.words, "chars" : res.chars, "url":res.url, "description":res.description, "location" : location, "server" : server, "server" : server, "postdata" : post_data}
        self.json_res.append(res_entry)

    def footer(self, summary):
        self.f.write(jjson.dumps(self.json_res))



@moduleman_plugin("header", "footer", "result")
class raw(BasePrinter):
    name = "raw"
    description = "Raw output format"
    category = ["default"]
    priority = 99

    def __init__(self, output):
        BasePrinter.__init__(self, output)

    def header(self, summary):
	self.f.write("Target: %s\n" % summary.url)
	self.f.write("Total requests: %d\n" % summary.total_req)
	self.f.write("==================================================================\n")
	self.f.write("ID	Response   Lines      Word         Chars          Payload    \n")
	self.f.write("==================================================================\n")

    def result(self, res):
	if res.exception:
	    self.f.write("XXX")
	else:
	    self.f.write("%05d:  C=%03d" % (res.nres, res.code))

	self.f.write("   %4d L\t   %5d W\t  %5d Ch\t  \"%s\"\n" % (res.lines, res.words, res.chars, res.description))

	for i in res.plugins_res:
		self.f.write("  |_ %s\n" % i.issue)


    def footer(self, summary):
	self.f.write("\n")
	self.f.write("Total time: %s\n" % str(summary.totaltime)[:8])

	if summary.backfeed() > 0:
	    self.f.write("Processed Requests: %s (%d + %d)\n" % (str(summary.processed())[:8], (summary.processed() - summary.backfeed()), summary.backfeed()))
	else:
	    self.f.write("Processed Requests: %s\n" % (str(summary.processed())[:8]))
	self.f.write("Filtered Requests: %s\n" % (str(summary.filtered())[:8]))
	self.f.write("Requests/sec.: %s\n" % str(summary.processed()/summary.totaltime if summary.totaltime > 0 else 0)[:8])
