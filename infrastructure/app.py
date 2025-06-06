from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    Duration,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class ChatbotStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB tables
        users_table = dynamodb.Table(
            self, "UsersTable",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )

        sessions_table = dynamodb.Table(
            self, "SessionsTable",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )

        interactions_table = dynamodb.Table(
            self, "InteractionsTable",
            partition_key=dynamodb.Attribute(
                name="interaction_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )

        # Add GSI for user_id-timestamp
        interactions_table.add_global_secondary_index(
            index_name="user_id-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Create S3 buckets
        knowledge_base_bucket = s3.Bucket(
            self, "KnowledgeBaseBucket",
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True
        )

        models_bucket = s3.Bucket(
            self, "ModelsBucket",
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True
        )

        # Create Lambda function
        chatbot_lambda = _lambda.Function(
            self, "ChatbotFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("app"),
            handler="api.main.handler",
            timeout=Duration.seconds(30),
            memory_size=1024,
            environment={
                "USERS_TABLE": users_table.table_name,
                "SESSIONS_TABLE": sessions_table.table_name,
                "INTERACTIONS_TABLE": interactions_table.table_name,
                "KNOWLEDGE_BASE_BUCKET": knowledge_base_bucket.bucket_name,
                "MODELS_BUCKET": models_bucket.bucket_name
            }
        )

        # Grant permissions
        users_table.grant_read_write_data(chatbot_lambda)
        sessions_table.grant_read_write_data(chatbot_lambda)
        interactions_table.grant_read_write_data(chatbot_lambda)
        knowledge_base_bucket.grant_read_write(chatbot_lambda)
        models_bucket.grant_read_write(chatbot_lambda)

        # Create API Gateway
        api = apigw.RestApi(
            self, "ChatbotApi",
            rest_api_name="Chatbot API",
            description="API for AI-powered chatbot",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200
            )
        )

        # Add resources and methods
        chat_resource = api.root.add_resource("chat")
        chat_resource.add_method(
            "POST",
            apigw.LambdaIntegration(chatbot_lambda)
        )

        users_resource = api.root.add_resource("users")
        users_resource.add_method(
            "POST",
            apigw.LambdaIntegration(chatbot_lambda)
        )

        user_history_resource = users_resource.add_resource("{user_id}").add_resource("history")
        user_history_resource.add_method(
            "GET",
            apigw.LambdaIntegration(chatbot_lambda)
        )

        # Add CORS
        api.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"]
        )

        # Output the API endpoint
        CfnOutput(
            self, "ApiEndpoint",
            value=api.url,
            description="API Gateway endpoint URL"
        )

        # Output the DynamoDB table names
        CfnOutput(
            self, "UsersTableName",
            value=users_table.table_name,
            description="Users DynamoDB table name"
        )

        CfnOutput(
            self, "SessionsTableName",
            value=sessions_table.table_name,
            description="Sessions DynamoDB table name"
        )

        CfnOutput(
            self, "InteractionsTableName",
            value=interactions_table.table_name,
            description="Interactions DynamoDB table name"
        )

        # Output the S3 bucket names
        CfnOutput(
            self, "KnowledgeBaseBucketName",
            value=knowledge_base_bucket.bucket_name,
            description="Knowledge base S3 bucket name"
        )

        CfnOutput(
            self, "ModelsBucketName",
            value=models_bucket.bucket_name,
            description="Models S3 bucket name"
        ) 