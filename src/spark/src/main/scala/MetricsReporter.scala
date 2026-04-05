import org.apache.spark.sql.streaming.StreamingQueryListener
import org.apache.spark.sql.streaming.StreamingQueryListener.{QueryIdleEvent, QueryProgressEvent, QueryStartedEvent, QueryTerminatedEvent}
import java.net.{HttpURLConnection, URL}
import java.io.OutputStream

class MetricsReporter(pushGatewayUrl: String, jobName: String) extends StreamingQueryListener {

  override def onQueryStarted(event: QueryStartedEvent): Unit = {
    println(s"Query started: ${event.id}")
  }

  override def onQueryProgress(event: QueryProgressEvent): Unit = {
    val progress = event.progress
    
    val metrics = s"""
      |# HELP spark_streaming_input_rows_per_second Input rate
      |# TYPE spark_streaming_input_rows_per_second gauge
      |spark_streaming_input_rows_per_second ${progress.inputRowsPerSecond}
      |# HELP spark_streaming_processed_rows_per_second Processing rate
      |# TYPE spark_streaming_processed_rows_per_second gauge
      |spark_streaming_processed_rows_per_second ${progress.processedRowsPerSecond}
      |# HELP spark_streaming_batch_duration_ms Batch duration
      |# TYPE spark_streaming_batch_duration_ms gauge
      |spark_streaming_batch_duration_ms ${progress.batchDuration}
      """.stripMargin

    pushMetrics(metrics)
  }

  override def onQueryTerminated(event: QueryTerminatedEvent): Unit = {
    println(s"Query terminated: ${event.id}")
  }

  override def onQueryIdle(event: QueryIdleEvent): Unit = {
    // No-op for now
  }

  private def pushMetrics(metrics: String): Unit = {
    try {
      val url = new URL(s"$pushGatewayUrl/metrics/job/$jobName")
      val connection = url.openConnection().asInstanceOf[HttpURLConnection]
      connection.setRequestMethod("POST")
      connection.setDoOutput(true)
      connection.setRequestProperty("Content-Type", "text/plain")

      val outputStream: OutputStream = connection.getOutputStream
      outputStream.write(metrics.getBytes("UTF-8"))
      outputStream.flush()
      outputStream.close()

      val responseCode = connection.getResponseCode
      if (responseCode >= 300) {
        println(s"Metrics push failed. Code: $responseCode")
      }
    } catch {
      case e: Exception =>
        println(s"Failed to push metrics to $pushGatewayUrl: ${e.getMessage}")
    }
  }
}
