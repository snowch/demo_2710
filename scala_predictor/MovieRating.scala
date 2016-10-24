import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf

import org.apache.spark.mllib.recommendation.ALS
import org.apache.spark.mllib.recommendation.MatrixFactorizationModel
import org.apache.spark.mllib.recommendation.Rating

object MovieRating {
  def main(args: Array[String]) {

    // the inputs to this spark job
    val model_path = args(0)
    val user_id = args(1).toInt
    val movie_id = args(2).toInt
    val output_path = args(3)

    val conf = new SparkConf().setAppName("Movie Rating")
    val sc = new SparkContext(conf)

    // load the saved model
    val model = MatrixFactorizationModel.load(sc, model_path)

    // predict a rating for the user_id and movie_id
    val predicted_rating = model.predict(user_id, movie_id)

    // package up the predicted rating so we can save it
    val rating = s"$user_id,$movie_id,$predicted_rating"
    val ratingRDD = sc.parallelize(Array(rating))

    // save the predicted rating
    ratingRDD.saveAsTextFile(output_path)

    sc.stop()
  }
}
