#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  6 07:41:54 2021

@author: anand
"""

import boto3
import time
import os, sys

import click
import json
import mimetypes



class Deploy2S3:
    def __init__(self, conf:dict):
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
        self.s3_session = boto3.Session(aws_access_key_id=conf["iam"]["id"],
                                   aws_secret_access_key=conf["iam"]["key"], 
                                   region_name=conf["s3"]["region"])
        self.s3 = self.s3_session.resource('s3')
        self.bucket = self.s3.Bucket(conf["s3"]["bucket"])
 
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
        for s_dir, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(s_dir, file)
                print(f"Uploading {file_path} to s3://{self.conf['s3']['bucket']}")
                s3_args={'ACL': 'public-read'}
                content_type= mimetypes.guess_type(file_path)[0]
                if content_type is not None:
                    s3_args['ContentType'] = content_type
    
                self.bucket.upload_file(file_path,
                                        file_path[len(folder):],
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
@click.argument('folder',  required=True,
                type=click.Path(exists=True, 
                                file_okay=True, 
                                dir_okay=True,
                                readable=True
                               ))

def main(config, folder):
    s3deploy=Deploy2S3(json.load(config))
    print("Uploading files to s3")
    s3deploy.push_to_s3(folder)
    print(f"Invalidating cloudfront cache - ID: {s3deploy.invalidate_distribution()}")

if __name__ == "__main__":
    main()
    
    
    
                    
                    


    