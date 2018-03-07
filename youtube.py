#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  3 15:35:44 2018

@author: shrey
"""

#!/usr/bin/python

# This sample executes a search request for the specified search term.
# Sample usage:
#   python search.py --q=surfing --max-results=10
# NOTE: To use the sample, you must provide a developer key obtained
#       in the Google APIs Console. Search for "REPLACE_ME" in this code
#       to find the correct place to provide that key..

from apiclient.discovery import build
#from apiclient.errors import HttpError
#from oauth2client.tools import argparser # removed by Dongho
import argparse
import csv
import unidecode

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyC-m97yXOult6NwHzKjVK2-6XuGDXCLzII"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def youtube_search(query):
    q = query
    maxResults = 1
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(q=q, part="id,snippet", maxResults=maxResults).execute() 
   

    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.
    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            #videos.append("%s (%s)" % (search_result["snippet"]["title"],search_result["id"]["videoId"]))
            title = search_result["snippet"]["title"]
            title = unidecode.unidecode(title)  # Dongho 08/10/16
            videoId = search_result["id"]["videoId"]
            video_response = youtube.videos().list(id=videoId,part="statistics").execute()
            for video_result in video_response.get("items",[]):
                viewCount = video_result["statistics"]["viewCount"]
            return viewCount
#                if 'likeCount' not in video_result["statistics"]:
#                    likeCount = 0
#                else:
#                    likeCount = video_result["statistics"]["likeCount"]
#                if 'dislikeCount' not in video_result["statistics"]:
#                    dislikeCount = 0
#                else:
#                    dislikeCount = video_result["statistics"]["dislikeCount"]
#                if 'commentCount' not in video_result["statistics"]:
#                    commentCount = 0
#                else:
#                    commentCount = video_result["statistics"]["commentCount"]
#                if 'favoriteCount' not in video_result["statistics"]:
#                    favoriteCount = 0
#                else:
#                    favoriteCount = video_result["statistics"]["favoriteCount"]
                    
            #csvWriter.writerow([title,videoId,viewCount,likeCount,dislikeCount,commentCount,favoriteCount])

    #csvFile.close()
  
if __name__ == "__main__":
#    parser = argparse.ArgumentParser(description='Search on YouTube')
#    parser.add_argument("--q", help="Search term", default="Google")
#    parser.add_argument("--max-results", help="Max results", default=25)
#    args = parser.parse_args()
    #try:
    csvFile = open('video_result.csv','w')
    csvWriter = csv.writer(csvFile)
    csvWriter.writerow(["title","viewCount"])
    
    tracks = []
    data = csv.reader(open('data/songDataSet.csv','r'))
    for i in data:
        tracks.append(i[15])
    subtracks = tracks[0:1000]
    for i in subtracks:
         csvWriter.writerow([i,youtube_search(i)])
        
    csvFile.close()
    #except HttpError, e:
    #    print ("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))