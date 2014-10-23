#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
#     Copyright (C) 2012 Team-XBMC
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#    This script is based on script.randomitems & script.wacthlist
#    Thanks to their original authors

# skin code:  <content target="video">plugin://plugin.test.me/</content>  ===NO ARGS
# skin code:  <content target="video">plugin://plugin.test.me?arg1=foo&arg2=bar</content> ===SUGGESTED BY JM
# skin code -CHECK THIS- <content target="video">plugin://plugin.test.me,arg1,arg2</content> ==USED IN PLEXBMC
# skin code liz.setProperty( "node.visible", [visibility condition] ) == sets visibility condition on per item basis

This is now in mainline.

@pecinko: You can set a:

* node:visible property that will be evaluated at display-time for switching items on and off dynamically 
    after initial list fill (i.e. after window load). The list itself is only refreshed on window load.

* node:target which can be used to define the target window/context. e.g. if listitem.path is
    'library://video/movies/titles' and node.target is 'video' it'll switch to the video window and 
    list the movie titles on click.

* node:target_url which can be used to override listitem.path in determining what to do when the item is clicked on. 
    This can be useful if you want listitem.path to point to a folder (to allow you to list it's content in another 
    container when the item has focus) while allowing the click on that item to do something different. 
    
    For example, the "Movies" button on confluence does this by other means - when you highlight Movies,
    the overview level of Movies is listed in the submenu underneath (Genres, Titles, Directors etc.) 
    
    This is equivalent to a different container listing library://video/movies/. However, when you click on Movies,
    you're taken directly to library://video/movies/titles.

Cheers,
Jonathan

'''

import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import random
import urllib
#import datetime
#import _strptime

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = xbmcaddon.Addon()
__addonversion__ = __addon__.getAddonInfo('version')
__addonid__      = __addon__.getAddonInfo('id')
__addonname__    = __addon__.getAddonInfo('name')
__localize__    = __addon__.getLocalizedString

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


def fetch_movies(limit):
    if not xbmc.abortRequested:
        #json_string = '{"jsonrpc": "2.0",  "id": 1, "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "originaltitle", "playcount", "year", "genre", "studio", "country", "tagline", "plot", "runtime", "file", "plotoutline", "lastplayed", "trailer", "rating", "resume", "art", "streamdetails", "mpaa", "director"], "limits": {"end": %d},' % limit
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties": ["title", "studio", "mpaa", "file", "art"], "sort": {"order": "descending", "method": "lastplayed"}, "filter": {"field": "inprogress", "operator": "true", "value": ""}, "limits": {"end": 25}}, "id": 1}' )

        #json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" } }}' %json_string)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query.has_key('result') and json_query['result'].has_key('tvshows'):
            count = 0
            for item in json_query['result']['tvshows']:
                if xbmc.abortRequested:
                    break
                count += 1
                json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"tvshowid": %d, "properties": ["title", "playcount", "plot", "season", "episode", "showtitle", "file", "lastplayed", "rating", "resume", "art", "streamdetails", "firstaired", "runtime"], "sort": {"method": "episode"}, "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": {"end": 1}}, "id": 1}' %item['tvshowid'])
                json_query2 = unicode(json_query2, 'utf-8', errors='ignore')
                json_query2 = simplejson.loads(json_query2)
                if json_query2.has_key('result') and json_query2['result'] != None and json_query2['result'].has_key('episodes'):
                    for item2 in json_query2['result']['episodes']:
                        episode = ("%.2d" % float(item2['episode']))
                        season = "%.2d" % float(item2['season'])
                        rating = str(round(float(item2['rating']),1))
                        episodeno = "s%se%s" %(season,episode)
                        art2 = item2['art']
                #seasonthumb = ''
                if (item2['resume']['position'] and item2['resume']['total']) > 0:
                    resume = "true"
                    played = '%s%%'%int((float(item2['resume']['position']) / float(item2['resume']['total'])) * 100)
                else:
                    resume = "false"
                    played = '0%'
                if item2['playcount'] >= 1:
                    watched = "true"
                else:
                    watched = "false"
                
                plot = item2['plot']
                art = item['art']
                path = media_path(item['file'])
                play = 'XBMC.RunScript(' + __addonid__ + ',episodeid=' + str(item2.get('episodeid')) + ')'
                streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(), item2['streamdetails'])
                
                #play = 'XBMC.RunScript(' + __addonid__ + ',movieid=' + str(item.get('movieid')) + ')'
                #streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(), item['streamdetails'])

                # create a list item
                liz = xbmcgui.ListItem(item['title'])
                liz.setInfo( type="Video", infoLabels={ "Title": item['title'] })
                #liz.setInfo( type="Video", infoLabels={ "OriginalTitle": item['originaltitle'] })
                #liz.setInfo( type="Video", infoLabels={ "Year": item['year'] })
                #liz.setInfo( type="Video", infoLabels={ "Genre": " / ".join(item['genre']) })
                #liz.setInfo( type="Video", infoLabels={ "Studio": item['studio'][0] })
                #liz.setInfo( type="Video", infoLabels={ "Country": item['country'][0] })
                liz.setInfo( type="Video", infoLabels={ "Plot": plot })
                
                """
                liz.setInfo( type="Video", infoLabels={ "PlotOutline": item['plotoutline'] })
                liz.setInfo( type="Video", infoLabels={ "Tagline": item['tagline'] })
                liz.setInfo( type="Video", infoLabels={ "Duration": item['runtime']/60 })
                liz.setInfo( type="Video", infoLabels={ "Rating": str(float(item['rating'])) })
                liz.setInfo( type="Video", infoLabels={ "MPAA": item['mpaa'] })
                liz.setInfo( type="Video", infoLabels={ "Director": " / ".join(item['director']) })
                liz.setInfo( type="Video", infoLabels={ "Trailer": item['trailer'] })
                """

                liz.setInfo( type="Video", infoLabels={ "Playcount": item2['playcount'] })
                liz.setProperty("resumetime", str(item2['resume']['position']))
                liz.setProperty("totaltime", str(item2['resume']['total']))

                liz.setThumbnailImage(art.get('poster', ''))
                liz.setProperty("fanart_image", art.get('fanart', ''))

                # TODO: support full art setting
                # self.WINDOW.setProperty("%s.%d.Art(poster)"     % (request, count), art.get('poster',''))
                # self.WINDOW.setProperty("%s.%d.Art(fanart)"     % (request, count), art.get('fanart',''))
                # self.WINDOW.setProperty("%s.%d.Art(clearlogo)"  % (request, count), art.get('clearlogo',''))
                # self.WINDOW.setProperty("%s.%d.Art(clearart)"   % (request, count), art.get('clearart',''))
                # self.WINDOW.setProperty("%s.%d.Art(landscape)"  % (request, count), art.get('landscape',''))
                # self.WINDOW.setProperty("%s.%d.Art(banner)"     % (request, count), art.get('banner',''))
                # self.WINDOW.setProperty("%s.%d.Art(discart)"    % (request, count), art.get('discart',''))  

                # TODO: can be done with liz.addStreamInfo()              
                # self.WINDOW.setProperty("%s.%d.VideoCodec"      % (request, count), streaminfo['videocodec'])
                # self.WINDOW.setProperty("%s.%d.VideoResolution" % (request, count), streaminfo['videoresolution'])
                # self.WINDOW.setProperty("%s.%d.VideoAspect"     % (request, count), streaminfo['videoaspect'])
                # self.WINDOW.setProperty("%s.%d.AudioCodec"      % (request, count), streaminfo['audiocodec'])
                # self.WINDOW.setProperty("%s.%d.AudioChannels"   % (request, count), str(streaminfo['audiochannels']))
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=item['file'],listitem=liz,isFolder=False)
        del json_query
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def media_path(path):
    # Check for stacked movies
    try:
        path = os.path.split(path)[0].rsplit(' , ', 1)[1].replace(",,",",")
    except:
        path = os.path.split(path)[0]
    # Fixes problems with rared movies and multipath
    if path.startswith("rar://"):
        path = [os.path.split(urllib.url2pathname(path.replace("rar://","")))[0]]
    elif path.startswith("multipath://"):
        temp_path = path.replace("multipath://","").split('%2f/')
        path = []
        for item in temp_path:
            path.append(urllib.url2pathname(item))
    else:
        path = [path]
    return path[0]

def media_streamdetails(filename, streamdetails):
    info = {}
    video = streamdetails['video']
    audio = streamdetails['audio']
    if '3d' in filename:
        info['videoresolution'] = '3d'
    elif video:
        videowidth = video[0]['width']
        videoheight = video[0]['height']
        if (video[0]['width'] <= 720 and video[0]['height'] <= 480):
            info['videoresolution'] = "480"
        elif (video[0]['width'] <= 768 and video[0]['height'] <= 576):
            info['videoresolution'] = "576"
        elif (video[0]['width'] <= 960 and video[0]['height'] <= 544):
            info['videoresolution'] = "540"
        elif (video[0]['width'] <= 1280 and video[0]['height'] <= 720):
            info['videoresolution'] = "720"
        elif (video[0]['width'] >= 1281 or video[0]['height'] >= 721):
            info['videoresolution'] = "1080"
        else:
            info['videoresolution'] = ""
    elif (('dvd') in filename and not ('hddvd' or 'hd-dvd') in filename) or (filename.endswith('.vob' or '.ifo')):
        info['videoresolution'] = '576'
    elif (('bluray' or 'blu-ray' or 'brrip' or 'bdrip' or 'hddvd' or 'hd-dvd') in filename):
        info['videoresolution'] = '1080'
    else:
        info['videoresolution'] = '1080'
    if video:
        info['videocodec'] = video[0]['codec']
        if (video[0]['aspect'] < 1.4859):
            info['videoaspect'] = "1.33"
        elif (video[0]['aspect'] < 1.7190):
            info['videoaspect'] = "1.66"
        elif (video[0]['aspect'] < 1.8147):
            info['videoaspect'] = "1.78"
        elif (video[0]['aspect'] < 2.0174):
            info['videoaspect'] = "1.85"
        elif (video[0]['aspect'] < 2.2738):
            info['videoaspect'] = "2.20"
        else:
            info['videoaspect'] = "2.35"
    else:
        info['videocodec'] = ''
        info['videoaspect'] = ''
    if audio:
        info['audiocodec'] = audio[0]['codec']
        info['audiochannels'] = audio[0]['channels']
    else:
        info['audiocodec'] = ''
        info['audiochannels'] = ''
    return info

    
log('script version %s started' % __addonversion__)
fetch_movies(3)
log('script version %s stopped' % __addonversion__)