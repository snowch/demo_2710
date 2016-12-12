To retrieve the VCAP_SERVICES info, ensure you have bound the services to the app in bluemix, then:

```
cf env music-recommender-flask
```

Note, normally all your services won't be in the same space in which case you can use the following advice:

http://stackoverflow.com/questions/40932208/can-i-inject-external-service-vcap-services-into-my-app


Find all ratings for user:

https://9aefd1f0-d288-4666-a12f-abd93ee724fc-bluemix.cloudant.com/ratingdb/_all_docs?inclusive_end=true&start_key=%22user_1%2F%22&end_key=%22user_1%2Fufff0%22
