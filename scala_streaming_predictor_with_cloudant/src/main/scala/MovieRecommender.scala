import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf
import org.apache.spark.sql.SQLContext
import org.apache.spark.storage.StorageLevel
import org.apache.spark.mllib.recommendation.MatrixFactorizationModel
import org.apache.spark.mllib.recommendation.ALS
import org.apache.spark.mllib.recommendation.Rating
import org.apache.log4j.LogManager

case class RatingWithTimestamp (
    user: Int,
    product: Int,
    rating: Double,
    timestamp: Long)

class MovieRecommender (sc:SparkContext) {
  
  val sqlContext = new SQLContext(sc)
  import sqlContext._
  
  val log = LogManager.getLogger(this.getClass)
  
  def buildModelAndRecommendMovies (userId:Int) = {
    val model = buildModel()
    recommendMovies(model, userId)
  }
  
  def buildModel() : MatrixFactorizationModel = {
    
    log.info(s"******** building model ********")
    
    val df = sqlContext.read.format("com.cloudant.spark").
      option("cloudant.host",sc.getConf.get("spark.cloudant_host")).
      option("cloudant.username", sc.getConf.get("spark.cloudant_user")).
      option("cloudant.password", sc.getConf.get("spark.cloudant_password")).
      load("ratingdb")
      
    df.cache()

    log.info(s"******** Found ${df.count()} records in Cloudant ********")
    
    
    val ratings = df.map { item => 
      val ids = item.getString(0).split("/")
      val user_id = ids(0).replaceAll("user_", "").toInt
      val product_id = ids(1).replaceAll("movie_", "").toInt
      val rating:Double = item.getString(2).toDouble
      
      Rating(user_id, product_id, rating)
    }.cache()
    
    log.info(s"******** Found ${ratings.count()} ratings ********")
    
    val rank = 50
    val numIterations = 20
    val lambdaParam = 0.1

    val model = ALS.train(ratings, rank, numIterations, lambdaParam)
    return model
  }
 
  def recommendMovies (model:MatrixFactorizationModel, userId:Int) = {
    
    log.info(s"******** Finding recommended movies for $userId ********")
    
    val ratings:Array[Rating] = model.recommendProducts(userId, 25)
    
    val timestamp: Long = System.currentTimeMillis / 1000
    
    val ratingsWithTimestamp:Array[RatingWithTimestamp] = 
      ratings.map { 
         rating => RatingWithTimestamp(rating.user, rating.product, rating.rating, timestamp) 
         }
    
    ratingsWithTimestamp.foreach { rating => 
      log.info(s"******** ${rating.user} ${rating.product} ${rating.rating} ${rating.timestamp} ********")
    }
    
    log.info(s"******** Found $ratings recommended movies for $userId ********")
    
    val rdd = sc.parallelize(ratingsWithTimestamp)
    
    val sqlContext = new SQLContext(sc)
    import sqlContext.implicits._
    
    log.info(s"******** Saving ratings to Cloudant ********")
    
    rdd.toDF.write.format("com.cloudant.spark").
      option("cloudant.host",sc.getConf.get("spark.cloudant_host")).
      option("cloudant.username", sc.getConf.get("spark.cloudant_user")).
      option("cloudant.password", sc.getConf.get("spark.cloudant_password")).
      save("recommendationdb")
      
    log.info(s"******** Ratings saved to Cloudant ********")
  }
  
}