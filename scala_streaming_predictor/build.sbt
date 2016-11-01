name := "Movie Rating"

version := "1.0"

scalaVersion := "2.10.5"

libraryDependencies ++= {
  val sparkVersion =  "1.6.0"
  Seq(
     "org.apache.spark" %% "spark-core" % sparkVersion % "provided",
     "org.apache.spark" %% "spark-sql" % sparkVersion % "provided",
     "org.apache.spark" %% "spark-streaming" % sparkVersion % "provided",
     "org.apache.spark" %% "spark-streaming-kafka" % sparkVersion % "provided",
     "org.apache.spark" %% "spark-mllib" % sparkVersion % "provided",
     "org.apache.kafka" % "kafka-log4j-appender" % "0.9.0.0",
     "org.apache.kafka" % "kafka-clients" % "0.9.0.0",
     "org.apache.kafka" %% "kafka" % "0.9.0.0"
    )
}

unmanagedBase <<= baseDirectory { base => base / "lib" }


