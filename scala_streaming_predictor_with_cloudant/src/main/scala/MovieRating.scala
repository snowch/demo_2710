import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf

import org.apache.spark.mllib.recommendation.ALS
import org.apache.spark.mllib.recommendation.MatrixFactorizationModel
import org.apache.spark.mllib.recommendation.Rating


import scala.collection.mutable.ArrayBuffer
import org.apache.spark.streaming.Duration
import org.apache.spark.streaming.Seconds
import org.apache.spark.streaming.StreamingContext
import com.ibm.cds.spark.samples.config.MessageHubConfig
import com.ibm.cds.spark.samples.dstream.KafkaStreaming.KafkaStreamingContextAdapter
import org.apache.kafka.common.serialization.Deserializer
import org.apache.kafka.common.serialization.StringDeserializer
import org.apache.kafka.common.serialization.StringSerializer
import org.apache.kafka.clients.producer.KafkaProducer
import org.apache.kafka.clients.producer.ProducerRecord
import java.util.UUID
import java.util.Properties
import scala.util.Try

import org.apache.spark.mllib.recommendation.ALS
import org.apache.spark.mllib.recommendation.MatrixFactorizationModel
import org.apache.spark.mllib.recommendation.Rating

import com.cloudant.spark.CloudantReceiver

object MovieRating {
  def main(args: Array[String]) {

    val conf = new SparkConf().setAppName("Movie Rating Streams")
    val sc = new SparkContext(conf)
    
    val ssc = new StreamingContext(sc, Seconds(10))
    
    val changes = ssc.receiverStream(new CloudantReceiver(Map(
      "cloudant.host" -> sc.getConf.get("spark.cloudant_host"),
      "cloudant.username" -> sc.getConf.get("spark.cloudant_user"),
      "cloudant.password" -> sc.getConf.get("spark.cloudant_password"),
      "database" -> "eventdb")))

    val recommender = new MovieRecommender(sc)
    
    changes.foreachRDD( rdd => {
        for(item <- rdd.collect().toArray) {
          
          if (item.startsWith("LOGIN_EVENT,")) {
            val _, userId = item.split(",")
            recommender.buildModelAndRecommendMovies(userId.toString.toInt)
          }
        }
    })
    ssc.start()
    ssc.awaitTermination() 
    ssc.stop(stopSparkContext=false, stopGracefully=true)
  }
}
