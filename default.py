#!/usr/bin/python
# -*- coding: utf-8 -*-

import html
import bs4
import urllib.request
import socket
import xbmc
import xbmcvfs
import xbmcaddon
import xbmcplugin
import xbmcgui
import sys
import re

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
xbox = xbmc.getCondVisibility("System.Platform.xbox")
translation = addon.getLocalizedString
forceViewMode = addon.getSetting("forceViewMode") == "true"
filter = addon.getSetting("filter") == "true"
filterRating = int(addon.getSetting("filterRating"))
filterThreshold = int(addon.getSetting("filterThreshold"))
icon = xbmcvfs.translatePath('special://home/addons/'+addonID+'/icon.png')
viewMode = str(addon.getSetting("viewMode"))
urlMain = "https://www.bestofyoutube.com"


def index():
    addDir(translation(30001), urlMain, "listVideos", icon)
    addDir(translation(30008), "", "bestOf", icon)
    addDir(translation(30006), urlMain+"/index.php?show=random", "listVideos", icon)
    addDir(translation(30007), "", "search", icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def bestOf():
    addDir(translation(30002), urlMain+"/index.php?show=week", "listVideos", "")
    addDir(translation(30003), urlMain+"/index.php?show=month", "listVideos", "")
    addDir(translation(30004), urlMain+"/index.php?show=year", "listVideos", "")
    addDir(translation(30005), urlMain+"/index.php?show=alltime", "listVideos", "")
    xbmcplugin.endOfDirectory(pluginhandle)


def search():
    keyboard = xbmc.Keyboard('', translation(30007))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos(urlMain+"/search.php?q="+search_string+"&s=video")


def playVideo(id):
    if xbox:
        url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
    else:
        url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def listVideos(url):
    content = getUrl(url)
    soup = bs4.BeautifulSoup(content, features="html.parser")

    for entry in soup.find_all("div", class_="main"):
        up = entry.find(lambda tag: tag.has_attr("name") and tag["name"] == "up").contents[0]
        up = float(up)
        down = entry.find(lambda tag: tag.has_attr("name") and tag["name"] == "down").contents[0]
        down = float(down)
        id = entry.find(lambda tag: tag.has_attr("src") and tag["src"].find("youtube.com/embed")>0)["src"].split("/")[-1]
        thumb = "http://img.youtube.com/vi/{}/0.jpg".format(id)
        title = cleanTitle(entry.select('div.title a')[0].text)
        if (up+down) > 0:
            percentage = int((up/(up+down))*100)
        else:
            percentage = 100
        if filter and (up+down) > filterThreshold and percentage < filterRating:
            continue

        title = "{} ({}%)".format(title, percentage)

        addLink(title, id,
                "playVideo",
                thumb,
                str(int(up)+int(down))+" Votes")

    pagination = soup.find("div", class_="pagination") or bs4.Tag(name='div')
    nextUrl = ""
    nextPage = ""
    for link in pagination.find_all('a'):
        url = urlMain + "/" + link["href"]
        if link.text.find("next »") >= 0:
            nextUrl = url
            nextPage = url[url.find("page=")+5:]
            if "&" in nextPage:
                nextPage = nextPage[:nextPage.find("&")]

    if nextUrl:
        if int(nextPage) % 2 == 0:
            listVideos(nextUrl)
        else:
            addDir(translation(30009), nextUrl, "listVideos", '')

    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')



def getUrl(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'BestOfYoutube XBMC Addon v2.1.1')
    response = urllib.request.urlopen(req)
    content = response.read()
    response.close()
    return content


def cleanTitle(title):
#    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")

#    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = html.unescape(title)
    title = title.strip()
    return title


def addLink(name, url, mode, iconimage, desc):
    u = sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': "DefaultVideo.png",  'thumb': iconimage})

    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': "DefaultVideo.png",  'thumb': iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


params = parameters_string_to_dict(sys.argv[2])
mode = urllib.parse.unquote_plus(params.get('mode', ''))
url = urllib.parse.unquote_plus(params.get('url', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'bestOf':
    bestOf()
elif mode == 'search':
    search()
else:
    index()
