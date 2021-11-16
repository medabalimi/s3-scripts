# AWS Policies
1. s3upload.json: Policy to provide access to an S3 bucket to a particular IAM role
2. cfinvalidate.json: Policy to provide access to an IAM role to invalidate a cloudfront cache

# s3-scripts
1. push2S3CFInv.py: push files to s3 bucket (policy: s3upload.json) and invalidate cache (policy: cfinvalidate.json). Requires config file in json format to be passed as the first argument. ```{
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
            }```
