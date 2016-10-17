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

    val quiz_show = Array((user_id, movie_id))
    val my_movie = sc.parallelize(quiz_show) 
    val individual_movie_rating_RDD = model.predict(my_movie)

    individual_movie_rating_RDD.saveAsTextFile(output_path)
  }
}
