To retrieve the VCAP_SERVICES info, ensure you have bound the services to the app in bluemix, then:

```
cf env music-recommender-flask
```

Note, normally all your services won't be in the same space in which case you can use the following advice:

http://stackoverflow.com/questions/40932208/can-i-inject-external-service-vcap-services-into-my-app
