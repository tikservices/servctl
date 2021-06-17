from .context import Context


def ping_sitemap(c: Context) -> None:
    # curl -c1 http://www.google.com/webmasters/sitemaps/ping?sitemap=
    # curl -c1 https://www.bing.com/webmaster/ping.aspx?siteMap=
    sitemap = f"https://{c.app.domains[0]}/sitemap.xml"
    c.sh.run(f"curl -s -L -o /dev/null 'http://www.google.com/ping?sitemap={sitemap}'")
    c.sh.run(f"curl -s -L -o /dev/null 'http://www.bing.com/ping?siteMap={sitemap}'")
