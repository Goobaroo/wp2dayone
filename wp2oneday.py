import string, os, sys, getopt
import urlparse
from urllib2 import urlopen
from urllib import urlretrieve
import feedparser
from HTMLParser import HTMLParser
from django.utils.html import strip_tags
import requests
import re

__author__ = 'Jason McLeod <jason@mcleods.me>'
__version__ = '1.0'
__date__ = '2013/07/13'

# Specal thanks to Ray Slakinski for the python refresher lesson. https://github.com/rays

links = []
imageTypes = ['.jpg', '.jpeg', '.png','.gif']

def get_image(url):
    r = requests.get(url)
    if r.status_code == 200:
        image_name = url.split('/')[-1]
        with open(image_name, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

def post_dayone(date, text=False, image=False, debug=False):
    cmd='dayone -d="'+date+'" '
    cleanup='rm -f dayone.txt'
    if image:
        cmd+='-p="'+image+'" '
        cleanup=' "'+image+'"'
    if text:
        with open('dayone.txt', 'w') as f:
            f.write(text.encode('utf-8'))
        cmd+='new < dayone.txt'
    else:
        cmd+='new < /dev/null'
    if debug:
        print "Command: %s" % cmd
    else:
        cmd+=' >/dev/null 2>&1'
        os.system(cmd)
        os.system(cleanup)

def parseXML(xml_file, debug=False):


    data = feedparser.parse(xml_file)

    # Grab the links for the blog, so we can filter image downloads to only
    # locally hosted content.
    if not data.entries:
        print "No entries found, please check that the filename is correct."
        sys.exit(5)
    for link in data.feed.links:
        links.append(link.href)
    p = 0
    print "Found %d entries." %len(data.entries)
    for entry in data.entries:
        if debug:
            print "Date: %s\tTitle: %s" % (entry.title, entry.wp_post_date)
        else:
            p += 1
            sys.stdout.write("\rAdding entry #%d of %d" % (p, len(data.entries)))
            sys.stdout.flush()
        for content in entry.content:
            text=entry.title+"\n\n"+strip_tags(content.value)
            imgCount = 0
            imgFound = False
            imgURLs = []
            # Find all the image and href tags.
            for imgURL in re.findall(r'img src="(.*?)"', content.value, re.IGNORECASE):
                if any(link in imgURL for link in links): # Only keep links from our domain.
                    if not "-tm" in imgURL: # Ignore thumbnails.
                        if imgURL not in imgURLs: # Only add a filename once.
                            imgURLs.append(imgURL)
                        imgFound = True
            for imgURL in re.findall(r'a href="(.*?)"', content.value, re.IGNORECASE):
                try:
                    if any(link in imgURL for link in links):
                        if imgURL not in imgURLs:
                            imgURLs.append(imgURL)
                        imgFound = True
                except:
                    pass
            if imgFound:
                for imgURL in imgURLs:
                    imgCount += 1
                    if debug: 
                        print "get_image: %s" % imgURL
                    else:
                        get_image(imgURL)
                    if imgCount == 1:
                        post_dayone(entry.wp_post_date, text, imgURL.split('/')[-1], debug)
                    elif imgCount > 1:
                        post_dayone(entry.wp_post_date, False, imgURL.split('/')[-1], debug)
            else:
                post_dayone(entry.wp_post_date, text, False, debug)
        if p == len(data.entries):
            print "\nDone."

def usage(sname):
    print """python %s [-ht] wordpress_export.xml
    Converts a Wordpress Export File to multiple html files.
    
    Options:
        -h,--help\tDisplays this information.
        -t,--test\tTest first, image urls and dayone calls will be outputted to screen.
    
    Note:
        If you want to import from only a single author, then export only that author.
        Same goes for importing a particular category.

    Example:
    python %s -t wordpress.xml
        """ % (sname, sname)


def main(argv):
    authors = False
    debug = False
    try:
		opts, args = getopt.getopt(
		    argv[1:], "ht", ["help", "test"])	
    except getopt.GetoptError, err:
		print str(err)
		usage(argv[0])
		sys.exit(2)
	
    for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage(argv[0])
			sys.exit()
		elif opt in ("-t", "--test"):
		    debug = True
		
    wp_XML = "".join(args)
	
    if wp_XML == "":
	    print "Error: Missing wordpress export file."
	    usage(argv[0])
	    sys.exit(3)
		
    parseXML(wp_XML, debug)
	

if __name__ == "__main__":
	main(sys.argv)
