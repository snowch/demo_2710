## Overview

This demo is to be presented at World of Watson 2016 - **"Accelerate Your Data Science Delivery with Integrated Notebooks and IBM BigInsights"**. The presentation slides are available here: [Presentation](./Presentation.pdf)

The purpose of this Data Science Experience (DSX) project is to show how data from IBM BigInsights on cloud can be analysed using DSX notebooks. This project uses the http://grouplens.org/datasets/movielens/ ml-1m dataset to build a movie recommendation model using PySpark. The ml-1m dataset consists of 1 million ratings from 6000 users on 4000 movies, it was released on 2/2003.

The movielens front end application where users can rate movies is available here: https://movielens.org/. A screenshot of the movielens user interface can be seen here: 


<div style="text-align:center" markdown="1">
<img src="https://movielens.org/images/site/main-screen.png" width="100%" style="float: left;" />
</div>


## Instructions

The project is split into a number of different notebooks that focus on specific steps.

If you don't want to use BigInsights, you can jump to Step 4, uncomment the first cell and run it to setup your data.


#### Step 1 - Provision BigInsights cluster

This notebook shows you how to provision a BigInsights on cloud cluster on Bluemix.<br>
[[Notebook link]](Step 01 - Provision BigInsights cluster.ipynb)<br>

#### Step 2 - Setup BigInsights with MovieLens data

The cluster is then loaded with the movielens ml-1m dataset using this notebook. <br>
[[Notebook link]](Step 02 - Setup BigInsights with MovieLens data.ipynb)

#### Step 3 - Import data from BigInsights to DSX

In this step, we import the BigInsights ml-1m dataset into DSX.<br>
[[Notebook link]](Step 03 - Import data from BigInsights to DSX.ipynb)

#### Step 4 - Exploratory analysis

In this notebook, we perform some basic exploratory analysis of the ml-1m dataset before we jump into machine learning.<br>
[[Notebook link]](Step 04 - Exploratory analysis.ipynb)

#### Step 5 - Train model

Here we use Spark's Machine Learning Library (MLlib) to train a machine learning model on the data.<br>
[[Notebook link]](Step 05 - Train model.ipynb)

#### Step 6 - Predict ratings

In this notebook, we simulate a new user's movie ratings and then use those ratings to predice movies for them.<br>
[[Notebook link]](Step 06 - Predict ratings.ipynb)

#### Step 7 - Export Spark model to BigInsights

This notebook exports the model built in the previous notebook. <br/>A scala spark job is then run on BigInsights that loads the model and predicts a rating for a user.<br>
[[Notebook link]](Step 07 - Export Spark model to BigInsights.ipynb)

#### Step 8 - Setup MessageHub (kafka)

This notebook uses the cloud foundry rest API to provision a MessageHub service instance.<br>
A kafka-python client is then used to produce and consume messages.<br>
[[Notebook link]](Step 08 - Setup MessageHub (kafka).ipynb)

#### Step 9 - Scala spark streaming on DSX

In this step we create a scala spark streaming listener than consumes the messages sent to MessageHub in the previous step.<br>
[[Notebook link]](Step 09 - Scala spark streaming on DSX.ipynb)

## Support

If you have any questions about this project, please contact me at <chris.snow@uk.ibm.com>


## Credits

- Thanks to University of Minnesota for allowing the movielens data to be used for this demo.
- This site was really useful https://github.com/jadianes/spark-movie-lens
