#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  6 07:41:54 2021

@author: anand
"""

import boto3
import time
import os
import sys

import click
import json
import mimetypes

from multiprocessing.pool import ThreadPool



class Deploy2S3:
    def __init__(self, conf:dict, threads):
        """
      

        Parameters
        ----------
        conf : dict
            DESCRIPTION.
        conf={
             "iam":
                  {"id": "S3_IAM_ID",
                   "key": "S3_IAM_KEY"
                  },
             "s3":
                  {
                   "bucket": "S3_BUCKET",
                   "region": "S3_REGION"
                  },
             "cloudfront": 
                 {
                 "id": "CLOUDFRONT_DISTRIBUTION_ID"
                 }
            }

        Returns
        -------
        None.

        """
        
        self.conf=conf
        print(conf["iam"]["id"], conf["iam"]["key"])
        self.s3_session = boto3.Session(aws_access_key_id=conf["iam"]["id"],
                                   aws_secret_access_key=conf["iam"]["key"], 
                                   region_name=conf["s3"]["region"])
        self.s3 = self.s3_session.resource('s3')
        self.bucket = self.s3.Bucket(conf["s3"]["bucket"])
        self.threads = threads
 
    def push_to_s3(self, folder):
        """

        Parameters
        ----------
        folder : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if not os.path.isfile(folder):
            file_paths= self.get_files(folder)
            pool = ThreadPool(processes=self.threads)
            pool.map(self.upload,file_paths)
        else:
            self.upload_file(folder)
    
    def get_files(self, folder):
        for s_dir, dirs, files in os.walk(folder):
                print(folder)
                for file in files:
                    print(file)
                    file_path = os.path.join(s_dir, file)
                    s3_path=file_path[len(folder):]
                    if sys.platform.startswith('win32'):
                        s3_path=s3_path.replace('\\','/')
                    s3_path=s3_path.lstrip('/')
                    yield file_path, s3_path
    
    def upload(self, file_paths):
        src_file_path,s3_path=file_paths
        self.upload_file(src_file_path,s3_path)
        
    def upload_file(self, src_file_path, s3_path=None):
        s3_args={} 
        if s3_path is None:
            
            s3_path=src_file_path.split('/')[-1]
        content_type= mimetypes.guess_type(src_file_path)[0]
        if content_type is not None:
            s3_args['ContentType'] = content_type
                
        print(f"Uploading {src_file_path} to s3://{self.conf['s3']['bucket']}")
        #print(src_file_path,s3_path,s3_args)

        self.bucket.upload_file(src_file_path,
                                s3_path,
                                ExtraArgs=s3_args)
        
    def invalidate_distribution(self):
        cf=boto3.client('cloudfront', 
                        aws_access_key_id=self.conf["iam"]["id"],
                        aws_secret_access_key=self.conf["iam"]["key"])
      
        status=cf.create_invalidation(DistributionId=self.conf["cloudfront"]["id"],
                                      InvalidationBatch={
                                          'Paths': {
                                              'Quantity': 1,
                                              'Items': ['/index.html']},
                                          'CallerReference':str(time.time()).replace(".","")
                                          }
                                      )
        return status['Invalidation']['Id']


@click.command()
@click.option('--config', '-c', required=True, type=click.File('rb'))
@click.option('--threads','-t', default=5, type=int)
@click.option('--cf-inv/--skip-cf-inv', default=True)
@click.option('--s3-push/--skip-s3-push', default=True)
@click.argument('folder',  required=True,
                type=click.Path(exists=True, 
                                file_okay=True, 
                                dir_okay=True,
                                readable=True
                               ))

def main(config, cf_inv,s3_push, threads, folder):
    
    s3deploy=Deploy2S3(json.load(config), threads)
    if s3_push:
        print("Uploading files to s3")
        s3deploy.push_to_s3(folder)
    if cf_inv:
        print(f"Invalidating cloudfront cache - ID: {s3deploy.invalidate_distribution()}")
        s3deploy.invalidate_distribution()

if __name__ == "__main__":
    main()
    
    
    
                    
                    


    
