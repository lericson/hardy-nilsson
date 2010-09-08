# This is where I put all the really specific stuff.
# encoding: utf-8
import os
import re
import urlparse
import urllib2

from BeautifulSoup import BeautifulSoup
from irken.dispatch import handler

from hnilsson.worker import HardyWorkerConnection

class CommonPeople(HardyWorkerConnection):
    greeting = filter(None, map(lambda v: v.strip().decode("utf-8"),
"""
det här är min tredje vecka på fredagsbilagan.
jag heter hardy. nilsson.
jag gör recensioner va. indierecensioner.
men jag har ju min egen tidning. mitt fanzine. common people.
jag ser eh common people som arenarockens antites.
common people är inte slitz.
common people är inte tracks.
common people är indie. indiepop.
""".split("\n")))
    allowable_domains = "youtube.com", "php.net", "collegehumor.com"
    url_re = re.compile(r"\b(https?://.+?\..+?/.+?)(?:$| )", re.I)

    @property
    def client_version(self):
        reffn = ".git/refs/heads/master"
        rv = "hardy-nilsson worker " + str(os.getpid())
        if os.path.exists(reffn):
            rev = open(reffn, "U").read().rstrip("\n")
            rv += " (master is %s)" % rev
        return rv

    #@handler("irc cmd join")
    #def say_greeting(self, cmd, target_name):
    #    if cmd.source == self:
    #        for line in self.greeting:
    #            self.send_cmd(None, "PRIVMSG", (target_name, line))

    @handler("irc cmd privmsg")
    def say_html_title(self, cmd, target_name, text):
        tell = cmd.source.nick if target_name.startswith("#") else None
        # XXX The bot needs to know its nickname for this to work.
        #reply_to = cmd.source if target_name == self.nick else target_name
        origin = target_name if target_name.startswith("#") else cmd.source.nick
        for url_text in self.url_re.findall(text):
            if not self._is_allowed_url(url_text):
                continue
            title = self._get_title(url_text)
            msg = "%s is %s" % (url_text, title.strip())
            msg = "%s: %s" % (tell, msg) if tell else msg
            self.send_cmd(None, "PRIVMSG", (origin, msg))

    @handler("irc cmd privmsg")
    def print_msg(self, cmd, target_name, text):
        cmd.source.i = getattr(cmd.source, "i", 0) + 1
        print "< %s #%03d> %s" % (cmd.source.nick, cmd.source.i, text)

    def _is_allowed_url(self, url_text):
        url = urlparse.urlsplit(url_text)
        for allowed in self.allowable_domains:
            if len(url.netloc) > len(allowed):
                if url.netloc.endswith("." + allowed):
                    return True
            else:
                if url.netloc == allowed:
                    return True
        return False

    def _get_title(self, url):
        rv = BeautifulSoup(urllib2.urlopen(url)).title.string
        rv = reduce(lambda v, w: v.replace(w, " "), "\r\n\t", rv)
        while "  " in rv:
            rv = rv.replace("  ", " ")
        return rv

if __name__ == "__main__":
    import sys
    from hnilsson.worker import main
    main(sys.argv[1], cls=CommonPeople)
