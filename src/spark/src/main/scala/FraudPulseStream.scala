import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._
import ml.dmlc.xgboost4j.scala.{DMatrix, XGBoost}
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.scala.DefaultScalaModule
import java.nio.file.{Files, Paths}
import scala.collection.JavaConverters._
import java.io.ByteArrayInputStream

case class FeatureConfig(feature_cols: Seq[String], type_mapping: Map[String, Int])

object FraudPulseStream {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder()
      .appName("FraudPulseStream")
      // Explicitly set checkpoint directories to avoid HDFS complaining locally
      .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoints")
      // Increase parallelism if we expand Kafka partitions
      .config("spark.sql.shuffle.partitions", "6")
      .getOrCreate()
      
    spark.sparkContext.setLogLevel("WARN")

    // Register Prometheus Listener if pushgateway is set
    val pushGateway = sys.env.getOrElse("PROMETHEUS_PUSHGATEWAY", "http://pushgateway:9091")
    spark.streams.addListener(new MetricsReporter(pushGateway, "fraudpulse-spark"))

    val kafkaBroker = sys.env.getOrElse("KAFKA_BROKER", "kafka:9092")
    val kafkaTopic = sys.env.getOrElse("KAFKA_TOPIC", "fraud-transactions")
    val mongoUri = sys.env.getOrElse("MONGO_URI", "mongodb://mongodb:27017/")
    val mongoDb = sys.env.getOrElse("MONGO_DB", "fraud_db")
    val mongoColl = sys.env.getOrElse("MONGO_COLLECTION", "transactions")
    val fraudThreshold = sys.env.getOrElse("FRAUD_THRESHOLD", "0.5").toDouble

    val schema = StructType(Array(
      StructField("step", IntegerType, true),
      StructField("type", StringType, true),
      StructField("amount", DoubleType, true),
      StructField("nameOrig", StringType, true),
      StructField("oldbalanceOrg", DoubleType, true),
      StructField("newbalanceOrig", DoubleType, true),
      StructField("nameDest", StringType, true),
      StructField("oldbalanceDest", DoubleType, true),
      StructField("newbalanceDest", DoubleType, true),
      StructField("isFraud", IntegerType, true),
      StructField("isFlaggedFraud", IntegerType, true)
    ))

    val mapper = new ObjectMapper()
    mapper.registerModule(DefaultScalaModule)
    
    val featureColsPath = "/app/models/feature_cols.json"
    val featureBytes = Files.readAllBytes(Paths.get(featureColsPath))
    val config = mapper.readValue(featureBytes, classOf[FeatureConfig])
    
    val typeMapping = config.type_mapping
    val broadcastTypeMapping = spark.sparkContext.broadcast(typeMapping)
    
    val modelPath = "/app/models/fraud_model.json"
    val modelBytes = Files.readAllBytes(Paths.get(modelPath))
    val broadcastModelBytes = spark.sparkContext.broadcast(modelBytes)

    val rawStream = spark.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", kafkaBroker)
      .option("subscribe", kafkaTopic)
      .option("startingOffsets", "latest")
      .option("failOnDataLoss", "false")
      .load()

    val parsedStream = rawStream.withColumn("data", from_json(col("value").cast("string"), schema))
      .withColumn("raw_value", col("value"))
      
    // Valid records
    val validStream = parsedStream.filter(col("data.step").isNotNull).select("data.*")
    
    // Invalid/Malformed records to DLQ
    val invalidStream = parsedStream.filter(col("data.step").isNull).select(col("raw_value").alias("value"))
    val dlqTopic = sys.env.getOrElse("KAFKA_DLQ_TOPIC", "fraud-transactions-dlq")
    invalidStream.writeStream
      .foreachBatch { (batchDF: org.apache.spark.sql.DataFrame, batchId: Long) =>
         DLQHandler.writeToDLQ(batchDF, dlqTopic, kafkaBroker)
      }
      .outputMode("append")
      .option("checkpointLocation", "/tmp/checkpoints/dlq")
      .start()

    val encodeTypeUDF = udf((t: String) => {
      val mapping = broadcastTypeMapping.value
      mapping.getOrElse(t, -1)
    })

    val enrichedStream = validStream
      .withColumn("balance_drained", when(col("newbalanceOrig") === 0, 1).otherwise(0))
      .withColumn("dest_balance_unchanged", when(col("newbalanceDest") === col("oldbalanceDest"), 1).otherwise(0))
      .withColumn("amount_to_balance_ratio", col("amount") / (col("oldbalanceOrg") + lit(1.0)))
      .withColumn("hour_of_day", col("step") % lit(24))
      .withColumn("is_transfer_or_cashout", when(col("type").isin("TRANSFER", "CASH_OUT"), 1).otherwise(0))
      .withColumn("type_encoded", encodeTypeUDF(col("type")))

    val predictFraudUDF = udf((featuresSeq: Seq[Double]) => {
      val booster = XGBoostModelLoader.getBooster(broadcastModelBytes.value)
      val featuresArray = featuresSeq.map(_.toFloat).toArray
      val dmatrix = new DMatrix(featuresArray, 1, featuresArray.length)
      val preds = booster.predict(dmatrix)
      preds(0)(0).toDouble
    })

    val scoredStream = enrichedStream.withColumn(
      "fraud_probability",
      predictFraudUDF(array(
        col("amount"), col("oldbalanceOrg"), col("newbalanceOrig"),
        col("oldbalanceDest"), col("newbalanceDest"),
        col("balance_drained").cast("double"), 
        col("dest_balance_unchanged").cast("double"),
        col("amount_to_balance_ratio"), 
        col("hour_of_day").cast("double"),
        col("is_transfer_or_cashout").cast("double"), 
        col("type_encoded").cast("double")
      ))
    )

    val ruleCondition = col("type").isin("TRANSFER", "CASH_OUT") &&
      col("newbalanceOrig") === 0 &&
      col("newbalanceDest") === col("oldbalanceDest") &&
      col("amount") > 200000

    val finalizedStream = scoredStream
      .withColumn("model_flag", col("fraud_probability") > lit(fraudThreshold))
      .withColumn("rule_engine_flag", ruleCondition)
      .withColumn("rule_triggered", when(col("rule_engine_flag"), lit("Large logical transfer with zeroed origin and unchanged destination.")).otherwise(lit("None")))
      .withColumn("fraud_flag", col("model_flag") || col("rule_engine_flag"))
      .withColumn("risk_level",
        when(col("fraud_probability") > 0.8 || col("rule_engine_flag"), lit("HIGH"))
        .when(col("fraud_probability") > lit(fraudThreshold), lit("MEDIUM"))
        .otherwise(lit("LOW"))
      )
      .withColumn("processed_at", current_timestamp())
      .withColumn("balance_drained", col("balance_drained") === 1)
      .withColumn("dest_balance_unchanged", col("dest_balance_unchanged") === 1)
      .withColumn("is_transfer_or_cashout", col("is_transfer_or_cashout") === 1)

    // Tumbling window: aggregate fraud rate per 5-minute intervals
    val windowedFraudRate = finalizedStream
      .withWatermark("processed_at", "10 minutes")
      .groupBy(
        window(col("processed_at"), "5 minutes"),
        col("type")
      )
      .agg(
        count("*").alias("total_transactions"),
        sum(when(col("fraud_flag"), 1).otherwise(0)).alias("fraud_count"),
        avg("fraud_probability").alias("avg_fraud_score"),
        sum("amount").alias("total_amount")
      )

    // Write windowed metrics to a separate topic (or just keep for analysis)
    // For this implementation, we will append it directly to console for observability
    windowedFraudRate.writeStream
      .outputMode("update")
      .format("console")
      .option("checkpointLocation", "/tmp/checkpoints/metrics")
      .start()

    val query = finalizedStream.writeStream
      .foreachBatch { (batchDF: org.apache.spark.sql.DataFrame, batchId: Long) =>
        println(s"Writing batch $batchId to MongoDB...")
        try {
          batchDF.write
            .format("mongodb")
            .mode("append")
            .option("database", mongoDb)
            .option("collection", mongoColl)
            .option("connection.uri", mongoUri)
            .save()
          println(s"Batch $batchId written successfully.")
        } catch {
          case e: Exception =>
            println(s"Error writing batch $batchId: ${e.getMessage}")
        }
      }
      .outputMode("append")
      .option("checkpointLocation", "/tmp/checkpoints")
      .start()

    query.awaitTermination()
  }
}

object XGBoostModelLoader {
  @transient private var booster: ml.dmlc.xgboost4j.scala.Booster = _

  def getBooster(modelBytes: Array[Byte]): ml.dmlc.xgboost4j.scala.Booster = {
    if (booster == null) {
      this.synchronized {
        if (booster == null) {
          booster = XGBoost.loadModel(new ByteArrayInputStream(modelBytes))
        }
      }
    }
    booster
  }
}
