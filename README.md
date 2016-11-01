## Overview

This demo is to be presented at World of Watson 2016 - **"Accelerate Your Data Science Delivery with Integrated Notebooks and IBM BigInsights"**. The presentation slides are available here: [Presentation](./Presentation.pdf)

- The purpose of this Data Science Experience (DSX) project is to show how data from IBM BigInsights on cloud can analysed using DSX notebooks. 
- This project uses the http://grouplens.org/datasets/movielens/ ml-1m dataset to build a movie recommendation model using PySpark.
- The ml-1m dataset consists of 1 million ratings from 6000 users on 4000 movies. It was released on 2/2003.

The movielens front end application where users can rate movies is available here: https://movielens.org/. <br/>
A screenshot of the movielens user interface can be seen here: 


<div style="text-align:center" markdown="1">
<img src="https://movielens.org/images/site/main-screen.png" width="50%" style="float: left;" />
</div>


## Instructions

The project is split into a number of different notebooks that focus on specific steps.

If you don't want to use BigInsights, you can jump to Step 4, uncomment the first cell and run it to setup your data.


#### Step 1 - Provision BigInsights cluster

This notebook shows you how to provision a BigInsights on cloud cluster on Bluemix.<br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/47cdae41-3c37-45ea-a8db-d769d09cf484/view?access_token=3b9b2ede82ac488e87841ecb7e2b4327a9048e3741c5371b5e926adffa59fb9b)<br>

#### Step 2 - Setup BigInsights with MovieLens data

The cluster is then loaded with the movielens ml-1m dataset using this notebook. <br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/648aa475-9487-4370-8529-e77c483e2df4/view?access_token=7b941a2e1fd5918ee47ae23142975a21c4b8c0219bc6fe2ee9f8c45697eee547)

#### Step 3 - Import data from BigInsights to DSX

In this step, we import the BigInsights ml-1m dataset into DSX.<br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/7ee23699-7654-40a3-aa84-069bdf04706d/view?access_token=582a2a971aed9b4176f75392dd9db162a166d3b33c3cdf872db0f92475215fe3)

#### Step 4 - Exploratory analysis

In this notebook, we perform some basic exploratory analysis of the ml-1m dataset before we jump into machine learning.<br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/4187e63f-b688-4a7f-b2be-409d60beac34/view?access_token=a2d278d7ca116266ab4085968fa1bb88ff86ba649369bc220889a5f36f50c1ef)

#### Step 5 - Train model

Here we use Spark's Machine Learning Library (MLlib) to train a machine learning model on the data.<br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/78ec9a65-b494-47dc-b8c3-5593dae524c9/view?access_token=733c997ae7e98e9eee7bea702c4e969640355db9f2108cef1911d63cfdad7475)

#### Step 6 - Predict ratings

In this notebook, we simulate a new user's movie ratings and then use those ratings to predice movies for them.<br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/2141592d-a551-4212-aa71-56558852e833/view?access_token=d82308453c0027068822216cdacc731ea4074f3431d1712dff68d164be4accd1)

#### Step 7 - Export Spark model to BigInsights

This notebook exports the model built in the previous notebook. <br/>A scala spark job is then run on BigInsights that loads the model and predicts a rating for a user.<br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/12438a01-acac-4b94-a1b8-663f3091cc4a/view?access_token=98baa449cbe5a3dfbea41055c236a490f450960cdb84468ba4f7fd54b7b14298)

#### Step 8 - Setup MessageHub (kafka)

This notebook uses the cloud foundry rest API to provision a MessageHub service instance.<br>
A kafka-python client is then used to produce and consume messages.<br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/9ce45745-aab4-47db-af3a-751cb1e79e74/view?access_token=42d36e4ef734f268778fae315eae78493995e7065f6f752427b7eabc6873b65f)

#### Step 9 - Scala spark streaming on DSX

In this step we create a scala spark streaming listener than consumes the messages sent to MessageHub in the previous step.<br>
[[Notebook link]](https://apsportal.ibm.com/analytics/notebooks/fea000bc-b422-49cb-a5d6-56ec40edfb48/view?access_token=6fa9ea382a2563ff25e4e0bf06eae997063e4ae11af44686e8750089b520c2a1)

## Support

If you have any questions about this project, please contact me at <chris.snow@uk.ibm.com>


## Credits

- Thanks to University of Minnesota for allowing the movielens data to be used for this demo.
- This site was really useful https://github.com/jadianes/spark-movie-lens
