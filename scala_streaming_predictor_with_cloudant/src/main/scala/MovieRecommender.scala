import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf
import org.apache.spark.sql.SQLContext
import org.apache.spark.storage.StorageLevel
import org.apache.spark.mllib.recommendation.MatrixFactorizationModel
import org.apache.spark.mllib.recommendation.ALS
import org.apache.spark.mllib.recommendation.Rating


class MovieRecommender (sc:SparkContext) {
  
  def buildModelAndRecommendMovies (userId:Int) = {
    val model = buildModel()
    recommendMovies(model, userId)
  }
  
  def buildModel() : MatrixFactorizationModel = {
    
    val sqlContext = new SQLContext(sc)
    import sqlContext._
    
    val df = sqlContext.read.format("com.cloudant.spark").
      option("cloudant.host",sc.getConf.get("spark.cloudant_host")).
      option("cloudant.username", sc.getConf.get("spark.cloudant_user")).
      option("cloudant.password", sc.getConf.get("spark.cloudant_password")).
      load("ratingdb")
    
    val ratings = df.map { item => 
      val ids = item.getString(0).split("/")
      val user_id = ids(0).replaceAll("user_", "").toInt
      val product_id = ids(1).replaceAll("movie_", "").toInt
      val rating:Double = item.getString(2).toDouble
      
      Rating(user_id, product_id, rating)
    }.cache() 
    
    val rank = 50
    val numIterations = 20
    val lambdaParam = 0.1

    val model = ALS.train(ratings, rank, numIterations, lambdaParam)
    return model
  }
 
  def recommendMovies (model:MatrixFactorizationModel, userId:Int) = {
    val ratings:Array[Rating] = model.recommendProducts(userId, 25)
    val rdd = sc.parallelize(ratings)
    
    val sqlContext = new SQLContext(sc)
    import sqlContext.implicits._
    
    rdd.toDF.write.format("com.cloudant.spark").
      option("cloudant.host",sc.getConf.get("spark.cloudant_host")).
      option("cloudant.username", sc.getConf.get("spark.cloudant_user")).
      option("cloudant.password", sc.getConf.get("spark.cloudant_password")).
      save("recommendationdb")
  }
  
}