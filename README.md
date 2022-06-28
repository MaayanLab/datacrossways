# DataCrossways

Launcher of data portal using the flask API and React fronted. Datacrossways is meant for deployment on Amazon AWS. I allows users to connect to a React frontend or access resources programmatically, by difectly interacting with the Datacrossways API. The frontend receives all information from the Datacrossways API.

The API accesses a Postgres database that persists information. The API needs access to some AWS resources and requires limited AWS permissions that are passes by a configuration file. Specifically the API requires to create S3 buckets and upload and retrieve files from it. 

<img src="https://user-images.githubusercontent.com/32603869/176254810-7a3bc02e-f47d-4c54-a939-9d1aef7d0df9.png" width="400">
