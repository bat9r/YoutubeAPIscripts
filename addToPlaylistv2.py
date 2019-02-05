#!/usr/bin/env python3.5

import os
import math
import google.oauth2.credentials
import easyargs

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

# Authorize the request and store authorization credentials.
def get_authenticated_service():
    client_secret_file = "client_secret.json"
    scopes = ['https://www.googleapis.com/auth/youtube.force-ssl',
              'https://www.googleapis.com/auth/youtube.readonly']
    api_service_name = 'youtube'
    api_version = 'v3'
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
    credentials = flow.run_console()
    return build(api_service_name, api_version, credentials = credentials)

def get_video_views_cout(client, video_ids):
    response = client.videos().list(
        part='statistics',
        id=','.join(video_ids)
    ).execute()
    video_list=[]
    for item in response.get("items"):
        tmp_dict={}
        tmp_dict["id"]=item.get("id")
        tmp_dict["views"]=int(item.get("statistics").get("viewCount"))
        video_list.append(tmp_dict)
    
    return video_list

def get_page_playlist_video_ids(client, playlist_from, page_token=''):
    response = client.playlistItems().list(
        part='id,contentDetails',
        maxResults=50,
        playlistId=playlist_from,
        pageToken=page_token
    ).execute()
    return response

def get_ids_from_page(page):
    ids=[]
    for item in page.get("items"):
        ids.append(item.get("contentDetails").get("videoId"))
    return ids

def get_nextPageToken_from_page(page):
    return page.get("nextPageToken")

def get_number_videos_from_page(page):
    total_results = int(page.get("pageInfo").get("totalResults"))
    print ("total_results", total_results)
    return total_results

def get_all_playlist_video_ids(client, playlist_from):
    page = get_page_playlist_video_ids(client, playlist_from)
    loops_count = math.floor(
        get_number_videos_from_page(page)/50
    )
    allVideos = get_video_views_cout(client, get_ids_from_page(page))
    next_page_token = get_nextPageToken_from_page(page)
    print ("loops_count", loops_count)
    for i in range(loops_count):
        page = get_page_playlist_video_ids(
            client, 
            playlist_from, 
            page_token=next_page_token
        )
        allVideos += get_video_views_cout(client, get_ids_from_page(page))
        next_page_token = get_nextPageToken_from_page(page)
    sorted_all_videos = sorted(allVideos, key=lambda k: k['views'], reverse=True)
    return sorted_all_videos 

def insert_video_in_playlist(client, video_id, playlist_to):
    response = client.playlistItems().insert(
        body = {
                    "snippet":
                    {
                        "playlistId": playlist_to,
                        "resourceId":
                        {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                },
        part='snippet'
    ).execute()
    print("[ADDED]\t", 
          "id:", response.get("snippet").get("resourceId").get("videoId"),
          "\ttitle:", response.get("snippet").get("title"))

def multiple_insert_in_playlist(client, playlist_from, playlist_to, count):
    for video in get_all_playlist_video_ids(client, playlist_from)[:int(count)]:
       insert_video_in_playlist(client, video.get("id"), playlist_to)


@easyargs    
def main(playlist_from, playlist_to, count=int):
    '''
    #playlist_from = "UUhsA0U7464b1zZIgQuW5Fhw"
    #playlist_to = "PLty5Aj9nVcZtnYFfJ4iR_Yt9hPUDWUDBj"
    '''
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print ("playlist_from:", playlist_from)
    print ("playlist_to:", playlist_to)
    print ("count:", count, type(count))

    client = get_authenticated_service()
    #print(get_all_playlist_video_ids(client, playlist_from)) 
    
    
    multiple_insert_in_playlist(client, playlist_from, playlist_to, count)
     
if __name__ == "__main__":
    main()
