name := "Movie Rating"

version := "1.0"

scalaVersion := "2.10.5"

libraryDependencies ++= {
  val sparkVersion =  "1.6.0"
  Seq(
     "org.apache.spark" %% "spark-core" % sparkVersion % "provided",
     "org.apache.spark" %% "spark-sql" % sparkVersion % "provided",
     "org.apache.spark" %% "spark-streaming" % sparkVersion % "provided",
     "org.apache.spark" %% "spark-mllib" % sparkVersion % "provided"
    )
}

resolvers += "Spark Packages Repo" at "http://dl.bintray.com/spark-packages/maven"
libraryDependencies += "cloudant-labs" % "spark-cloudant" % "1.6.4-s_2.10"

assemblyMergeStrategy in assembly := {
  case PathList("org", "apache", "spark", xs @ _*) => MergeStrategy.first
  case PathList("scala", xs @ _*) => MergeStrategy.discard
  case PathList("META-INF", "maven", "org.slf4j", xs @ _* ) => MergeStrategy.first
  case x =>
    val oldStrategy = (assemblyMergeStrategy in assembly).value
    oldStrategy(x)
}

unmanagedBase <<= baseDirectory { base => base / "lib" }

assemblyOption in assembly := (assemblyOption in assembly).value.copy(includeScala = false)

