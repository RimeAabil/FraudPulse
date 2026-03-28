name := "fraudpulse"
version := "1.0"
scalaVersion := "2.12.18"

val sparkVersion = "3.5.3"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-sql" % sparkVersion % "provided",
  "org.apache.spark" %% "spark-sql-kafka-0-10" % sparkVersion,
  "org.mongodb.spark" %% "mongo-spark-connector" % "10.6.1",
  "ml.dmlc" % "xgboost4j_2.12" % "2.0.3",
  "com.fasterxml.jackson.module" %% "jackson-module-scala" % "2.15.2"
)
