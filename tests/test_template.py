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

    def test_defines_encrypted_on_demand_table(self):
        self.assertIn("Type: AWS::DynamoDB::Table", self.template)
        self.assertIn("BillingMode: PAY_PER_REQUEST", self.template)
        self.assertIn("SSEEnabled: true", self.template)
        self.assertIn("USER_TABLE_NAME: !Ref DataTable", self.template)

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
        self.assertIn("greetings_bot.queue_worker.handle_event", self.template)
        self.assertIn("ReportBatchItemFailures", self.template)
        self.assertEqual(self.template.count("SqsManagedSseEnabled: true"), 2)


if __name__ == "__main__":
    unittest.main()
