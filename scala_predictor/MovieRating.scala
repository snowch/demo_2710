import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf

import org.apache.spark.mllib.recommendation.ALS
import org.apache.spark.mllib.recommendation.MatrixFactorizationModel
import org.apache.spark.mllib.recommendation.Rating

object MovieRating {
  def main(args: Array[String]) {

    val model_path = args(0)
    val user_id = args(1).toInt
    val movie_id = args(2).toInt
    val output_path = args(3)

    val conf = new SparkConf().setAppName("Movie Rating")
    val sc = new SparkContext(conf)

    val model = MatrixFactorizationModel.load(sc, model_path)
    val predicted_rating = model.predict(user_id, movie_id)
    val response = sc.parallelize(s"user_id: $user_id, movie_id: $movie_id, predict_rating: $predicted_rating")
    response.saveAsTextFile(output_path)

    sc.stop()
  }
}
