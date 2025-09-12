import unittest
from pathlib import Path


class SamTemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = Path("template.yaml").read_text()

    def test_defines_python_webhook_function(self):
        self.assertIn("Type: AWS::Serverless::Function", self.template)
        self.assertIn("Runtime: python3.9", self.template)
        self.assertIn("greetings_bot.lambda_handler.handle_event", self.template)

    def test_exposes_post_webhook(self):
        self.assertIn("Path: /telegram/webhook", self.template)
        self.assertIn("Method: post", self.template)

    def test_bounds_webhook_weather_requests(self):
        self.assertEqual(self.template.count("WEATHER_TIMEOUT_SECONDS: '5'"), 2)
        self.assertEqual(self.template.count("WEATHER_MAX_CALLS: '20'"), 2)
        self.assertEqual(self.template.count("WEATHER_CACHE_MINUTES: '60'"), 2)
        self.assertEqual(self.template.count("WEATHER_STALE_HOURS: '24'"), 2)

    def test_keeps_information_requests_disabled(self):
        self.assertIn("InformationRequestsEnabled:", self.template)
        self.assertIn("Default: 'false'", self.template)
        self.assertIn(
            "INFO_REQUESTS_ENABLED: !Ref InformationRequestsEnabled",
            self.template,
        )

    def test_configures_the_bedrock_information_model(self):
        self.assertIn("BedrockModelId:", self.template)
        self.assertIn("Default: amazon.titan-text-lite-v1", self.template)
        self.assertIn("BEDROCK_MODEL_ID: !Ref BedrockModelId", self.template)

    def test_bounds_the_bedrock_runtime_timeout(self):
        self.assertIn("BedrockTimeoutSeconds:", self.template)
        self.assertIn(
            "BEDROCK_TIMEOUT_SECONDS: !Ref BedrockTimeoutSeconds",
            self.template,
        )
        self.assertIn("Default: 8", self.template)

    def test_limits_bedrock_access_to_the_selected_model(self):
        self.assertIn("Action: bedrock:InvokeModel", self.template)
        self.assertIn(
            "bedrock:${AWS::Region}::foundation-model/${BedrockModelId}",
            self.template,
        )

    def test_configures_weekly_information_allowance(self):
        self.assertIn("InformationWeeklyLimit:", self.template)
        self.assertIn("INFO_WEEKLY_LIMIT: !Ref InformationWeeklyLimit", self.template)
        self.assertIn("MinValue: 1", self.template)
        self.assertIn("MaxValue: 100", self.template)

    def test_allows_atomic_quota_updates(self):
        self.assertIn("dynamodb:UpdateItem", self.template)

    def test_defines_protected_admin_read_routes(self):
        self.assertIn("AdminFunction:", self.template)
        self.assertIn("greetings_bot.admin_handler.handle_event", self.template)
        self.assertIn("Path: /admin/dashboard", self.template)
        self.assertIn("Path: /admin/health", self.template)
        self.assertIn("Path: /admin/stats", self.template)
        self.assertIn("Path: /admin/users", self.template)
        self.assertIn("Path: /admin/users/{id}", self.template)
        self.assertIn("Path: /admin/users/{id}/export", self.template)
        self.assertGreaterEqual(self.template.count("Method: get"), 5)

    def test_defines_confirmed_user_deletion_routes(self):
        self.assertIn("Path: /admin/users/{id}/deletion", self.template)
        self.assertIn(
            "Path: /admin/users/{id}/deletion/confirm", self.template
        )
        self.assertIn(
            "Path: /admin/users/{id}/deletion/execute", self.template
        )
        admin = self.template.split("AdminFunction:", 1)[1].split(
            "GreetingDispatcherFunction:", 1
        )[0]
        self.assertIn("dynamodb:PutItem", admin)
        self.assertIn("dynamodb:Query", admin)
        self.assertIn("dynamodb:DeleteItem", admin)
        self.assertIn("scheduler:DeleteSchedule", admin)
        self.assertIn("SCHEDULER_GROUP: !Ref ReminderScheduleGroup", admin)

    def test_exposes_dashboard_operation_pages(self):
        self.assertIn("Path: /admin/dashboard/users", self.template)
        self.assertIn("Path: /admin/dashboard/users/{id}", self.template)
        self.assertIn("Path: /admin/dashboard/config", self.template)
        self.assertIn("Path: /admin/dashboard/delivery", self.template)
        self.assertIn(
            "Path: /admin/dashboard/delivery/redrive", self.template
        )

    def test_limits_admin_table_access_to_reads(self):
        self.assertIn("- dynamodb:Scan", self.template)
        self.assertIn("- dynamodb:GetItem", self.template)

    def test_defines_delivery_admin_routes_and_queue_access(self):
        self.assertIn("Path: /admin/delivery", self.template)
        self.assertIn("Path: /admin/delivery/redrive", self.template)
        self.assertIn("DELIVERY_DLQ_URL: !Ref DeliveryDeadLetterQueue", self.template)
        self.assertIn("DELIVERY_DLQ_ARN: !GetAtt DeliveryDeadLetterQueue.Arn", self.template)
        self.assertIn("sqs:GetQueueAttributes", self.template)
        self.assertIn("sqs:StartMessageMoveTask", self.template)
        self.assertIn("sqs:ReceiveMessage", self.template)
        self.assertIn("sqs:DeleteMessage", self.template)
        self.assertIn("sqs:SendMessage", self.template)

    def test_passes_the_hidden_admin_token_and_shared_table(self):
        self.assertIn("AdminApiToken:", self.template)
        self.assertIn("MinLength: 24", self.template)
        self.assertIn("ADMIN_API_TOKEN: !Ref AdminApiToken", self.template)
        self.assertIn("USER_TABLE_NAME: !Ref DataTable", self.template)

    def test_defines_encrypted_on_demand_table(self):
        self.assertIn("Type: AWS::DynamoDB::Table", self.template)
        self.assertIn("BillingMode: PAY_PER_REQUEST", self.template)
        self.assertIn("SSEEnabled: true", self.template)
        self.assertIn("USER_TABLE_NAME: !Ref DataTable", self.template)

    def test_expires_weather_cache_records(self):
        self.assertIn("TimeToLiveSpecification:", self.template)
        self.assertIn("AttributeName: expires_at", self.template)
        self.assertIn("Enabled: true", self.template)

    def test_bounds_delivery_record_retention(self):
        self.assertIn("DeliveryHistoryDays:", self.template)
        self.assertIn("DELIVERY_HISTORY_DAYS: !Ref DeliveryHistoryDays", self.template)
        self.assertIn("DeliveryReceiptDays:", self.template)
        self.assertIn("DELIVERY_RECEIPT_DAYS: !Ref DeliveryReceiptDays", self.template)

    def test_limits_webhook_table_permissions(self):
        self.assertIn("dynamodb:GetItem", self.template)
        self.assertIn("dynamodb:PutItem", self.template)
        self.assertIn("dynamodb:Scan", self.template)
        self.assertIn("dynamodb:Query", self.template)
        self.assertIn("dynamodb:DeleteItem", self.template)
        self.assertNotIn("dynamodb:*", self.template)

    def test_defines_minute_dispatcher(self):
        self.assertIn("GreetingDispatcherFunction:", self.template)
        self.assertIn("greetings_bot.scheduled_handler.handle_event", self.template)
        self.assertIn("Schedule: rate(1 minute)", self.template)
        self.assertIn("DISPATCH_BATCH_SIZE: '100'", self.template)

    def test_defines_due_reminder_index(self):
        self.assertIn("IndexName: DueIndex", self.template)
        self.assertIn("AttributeName: gsi1pk", self.template)
        self.assertIn("AttributeName: gsi1sk", self.template)
        self.assertIn("${DataTable.Arn}/index/*", self.template)

    def test_defines_targeted_reminder_scheduler(self):
        self.assertIn("Type: AWS::Scheduler::ScheduleGroup", self.template)
        self.assertIn("greetings_bot.reminder_handler.handle_event", self.template)
        self.assertIn("Service: scheduler.amazonaws.com", self.template)
        self.assertIn("Action: lambda:InvokeFunction", self.template)
        self.assertIn("scheduler:CreateSchedule", self.template)
        self.assertIn("Action: iam:PassRole", self.template)

    def test_defines_delivery_queue_and_dlq(self):
        self.assertIn("DeliveryDeadLetterQueue:", self.template)
        self.assertIn("deadLetterTargetArn: !GetAtt DeliveryDeadLetterQueue.Arn", self.template)
        self.assertIn("maxReceiveCount: 5", self.template)
        self.assertIn("VisibilityTimeout: 120", self.template)
        self.assertIn("greetings_bot.queue_worker.handle_event", self.template)
        self.assertIn("ReportBatchItemFailures", self.template)
        self.assertEqual(self.template.count("SqsManagedSseEnabled: true"), 2)

    def test_alarms_on_delivery_failures_and_dead_letters(self):
        self.assertEqual(self.template.count("Type: AWS::CloudWatch::Alarm"), 4)
        self.assertIn("MetricName: Failed", self.template)
        self.assertIn("Value: delivery", self.template)
        self.assertIn("MetricName: ApproximateNumberOfMessagesVisible", self.template)
        self.assertIn("Value: !GetAtt DeliveryDeadLetterQueue.QueueName", self.template)
        self.assertEqual(self.template.count("TreatMissingData: notBreaching"), 4)

    def test_alarms_on_delivery_worker_errors(self):
        self.assertIn("Namespace: AWS/Lambda", self.template)
        self.assertIn("MetricName: Errors", self.template)
        self.assertIn("Value: !Ref DeliveryWorkerFunction", self.template)

    def test_alarms_on_weather_provider_errors(self):
        self.assertIn("WeatherProviderErrorAlarm:", self.template)
        self.assertIn("MetricName: ProviderError", self.template)
        self.assertIn("Value: weather", self.template)


if __name__ == "__main__":
    unittest.main()
