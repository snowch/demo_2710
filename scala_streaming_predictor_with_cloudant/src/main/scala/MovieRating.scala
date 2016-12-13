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
import org.apache.log4j.LogManager

import org.apache.spark.mllib.recommendation.ALS
import org.apache.spark.mllib.recommendation.MatrixFactorizationModel
import org.apache.spark.mllib.recommendation.Rating



object MovieRating {
  def main(args: Array[String]) {
    
    val log = LogManager.getLogger(this.getClass)
    
    log.info("*********** in MovieRating *********")

    val conf = new SparkConf().setAppName("Movie Rating Streams")
    val sc = new SparkContext(conf)
    
    val kafkaProps = new MessageHubConfig
    
    kafkaProps.setConfig("bootstrap.servers",   sc.getConf.get("spark.bootstrap_servers"))
    kafkaProps.setConfig("kafka.user.name",     sc.getConf.get("spark.sasl_username"))
    kafkaProps.setConfig("kafka.user.password", sc.getConf.get("spark.sasl_password"))
    kafkaProps.setConfig("kafka.topic",         sc.getConf.get("spark.messagehub_topic_name"))
    kafkaProps.setConfig("api_key",             sc.getConf.get("spark.api_key"))
    kafkaProps.setConfig("kafka_rest_url",      sc.getConf.get("spark.kafka_rest_url"))
    
    kafkaProps.createConfiguration()
    
    val properties = new Properties()
    kafkaProps.toImmutableMap.foreach {case (key, value) => properties.setProperty (key, value)}
    properties.setProperty("value.serializer", "org.apache.kafka.common.serialization.StringSerializer")
    
    val ssc = new StreamingContext( sc, Seconds(10) )
    
    val stream = ssc.createKafkaStream[String, String, StringDeserializer, StringDeserializer](
                         kafkaProps,
                         List(kafkaProps.getConfig("kafka.topic"))
                         )
                         
    val recommender = new MovieRecommender(sc)
                             
    val userLogoutEvents = stream.
                        filter(_._2.contains(",")).
                        map(_._2.split(","))
    
    userLogoutEvents.foreachRDD( rdd => {
        for(item <- rdd.collect().toArray) {
          
            log.info(s"*********** in foreach : item ${item(0)} ${item(1)} *********")
          
            if (item(0) == "LOGIN_EVENT") {
                val userId = item(1).toInt
                
                log.info(s"*********** LOGIN_EVENT received for $userId *********")
                
                recommender.buildModelAndRecommendMovies(userId)
                
                log.info(s"*********** finished buildModelAndRecommendMovies for $userId *********")
            }
        }
    })
    ssc.start()
    ssc.awaitTermination() 
    ssc.stop(stopSparkContext=false, stopGracefully=true)
  }
}
