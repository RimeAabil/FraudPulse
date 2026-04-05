import org.apache.spark.sql.{DataFrame, SparkSession}

object DLQHandler {
  def writeToDLQ(df: DataFrame, topic: String, broker: String): Unit = {
    try {
      df.selectExpr("CAST(value AS STRING) AS value")
        .write
        .format("kafka")
        .option("kafka.bootstrap.servers", broker)
        .option("topic", topic)
        .save()
      println(s"Successfully routed failed records to DLQ: $topic")
    } catch {
      case e: Exception =>
        println(s"CRITICAL: Failed to write to DLQ ($topic): ${e.getMessage}")
    }
  }
}
