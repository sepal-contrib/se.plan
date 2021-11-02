#!/usr/bin/env python3
from pathlib import Path

import ee
import io
from googleapiclient.http import MediaIoBaseDownload
from apiclient import discovery

import logging

logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


class gdrive(object):
    def __init__(self):

        self.initialize = ee.Initialize()
        self.credentials = ee.Credentials()
        self.service = discovery.build(
            serviceName="drive",
            version="v3",
            cache_discovery=False,
            credentials=self.credentials,
        )

    def tasks_list(self):
        """for debugging purpose, print the list of all the tasks in gee"""
        service = self.service

        tasks = service.tasks().list(tasklist="@default", q="trashed = false").execute()

        for task in tasks["items"]:
            print(task["title"])

    def print_file_list(self):
        """for debugging purpose, print the list of all the file in the Gdrive"""
        service = self.service

        results = (
            service.files()
            .list(pageSize=50, fields="nextPageToken, files(id, name)")
            .execute()
        )
        items = results.get("files", [])
        if not items:
            print("No files found.")
        else:
            print("Files:")
            for item in items:
                print("{0} ({1})".format(item["name"], item["id"]))

    def get_items(self, mimeType="image/tiff"):
        """get all the items in the Gdrive, items will have 2 columns, 'name' and 'id'"""

        service = self.service

        # get list of files
        results = (
            service.files()
            .list(
                q=f"mimeType='{mimeType}' and trashed = false",
                pageSize=1000,
                fields="nextPageToken, files(id, name)",
            )
            .execute()
        )
        items = results.get("files", [])

        return items

    def get_files(self, file_name):
        """look for the file_name patern in my Gdrive files and retreive a list of Ids"""

        items = self.get_items()
        files = []
        for item in items:
            if item["name"].startswith(file_name):
                files.append({"id": item["id"], "name": item["name"]})

        return files

    def download_files(self, files, local_path):
        """download the selected files to the selected local_path"""

        service = self.service

        # cast as path
        local_path = Path(local_path)

        local_files = []
        for fId in files:
            request = service.files().get_media(fileId=fId["id"])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # print('Download %d%%.' % int(status.progress() * 100))

            local_file = local_path / fId["name"]
            with local_file.open("wb") as fo:
                fo.write(fh.getvalue())

            local_files.append(local_file)

        return local_files

    def delete_files(self, files):

        service = self.service

        for f in files:
            service.files().delete(fileId=f["id"]).execute()

        return
